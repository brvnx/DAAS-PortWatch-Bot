import asyncio
#import nest_asyncio  
#nest_asyncio.apply() 
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,   
    MessageHandler,
    filters          
)

import os
from dotenv import load_dotenv


# === CONFIGURAÇÕES ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = os.getenv("URL")

ultima_lista = []
detalhes_navios = {}

# === FUNÇÕES DE SCRAPING ===
def obter_manobras():
    """Lê a tabela de manobras e retorna lista de dicionários"""
    resposta = requests.get(URL)
    resposta.encoding = "utf-8"
    soup = BeautifulSoup(resposta.text, "html.parser")

    tabela = soup.find("table")
    if not tabela:
        return []

    linhas = tabela.find_all("tr")[1:]
    manobras = []
    for linha in linhas:
        colunas = [td.text.strip() for td in linha.find_all("td")]
        if len(colunas) >= 15:
            manobra = {
                "nome": colunas[0],
                "bandeira": colunas[1],
                "indicativo": colunas[2],
                "calado": colunas[3],
                "dwt": colunas[4],
                "imo": colunas[5],
                "loa": colunas[6],
                "boca": colunas[7],
                "agencia": colunas[8],
                "rebocadores": colunas[9],
                "data": colunas[10],
                "hora": colunas[11],
                "tipo": colunas[12],
                "de": colunas[13],
                "berco": colunas[14],
            }
            manobras.append(manobra)
    return manobras


# === FORMATAÇÃO ===
def formatar_alerta(m):
    """Mensagem curta para alertas automáticos"""
    return (
        f"🚢 *Nova manobra detectada!*\n\n"
        f"🛳️ *Navio:* {m['nome']}\n"
        f"🚩 *Bandeira:* {m['bandeira']}\n"
        f"⚓ *Tipo:* {m['tipo']}\n"
        f"🏗️ *Berço:* {m['berco']}\n"
        f"📅 *Data:* {m['data']} | 🕓 *Hora:* {m['hora']}\n"
        f"🏢 *Agência:* {m['agencia']}"
    )


def formatar_detalhes(m):
    """Mensagem longa para o comando /detalhes"""
    return (
        f"🚢 *Detalhes da manobra: {m['nome']}*\n\n"
        f"🚩 *Bandeira:* {m['bandeira']}\n"
        f"📞 *Indicativo:* {m['indicativo']}\n"
        f"⚖️ *DWT:* {m['dwt']} | *Calado:* {m['calado']} m\n"
        f"📏 *LOA:* {m['loa']} m | *Boca:* {m['boca']} m\n"
        f"🆔 *IMO:* {m['imo']}\n"
        f"🏢 *Agência:* {m['agencia']}\n"
        f"🛟 *Rebocadores:* {m['rebocadores']}\n"
        f"⚓ *Tipo:* {m['tipo']}\n"
        f"📍 *De:* {m['de']}\n"
        f"🏗️ *Berço:* {m['berco']}\n"
        f"📅 *Data:* {m['data']} | 🕓 *Hora:* {m['hora']}"
    )


# === MONITORAMENTO AUTOMÁTICO ===
async def verificar_novidades(app):
    """Verifica o site e envia novas manobras para o grupo"""
    global ultima_lista, detalhes_navios
    try:
        atual = obter_manobras()
        if not ultima_lista:
            ultima_lista = atual
            detalhes_navios = {m["nome"].lower(): m for m in atual}
            print("Primeira checagem concluída.")
            return

        novos = [m for m in atual if m not in ultima_lista]
        if novos:
            for m in novos:
                detalhes_navios[m["nome"].lower()] = m
                msg = formatar_alerta(m)
                await app.bot.send_message(chat_id=int(CHAT_ID), text=msg, parse_mode="Markdown")
            ultima_lista = atual
            print(f"{len(novos)} novas manobras enviadas.")
        else:
            print("Nenhuma novidade encontrada.")
    except Exception as e:
        print(f"Erro ao verificar site: {e}")

# === COMANDO /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os comandos disponíveis"""
    msg = (
        "🤖 *DAAS PortWatch Bot*\n\n"
        "Comandos disponíveis:\n"
        "/help - Mostra esta lista de comandos\n"
        "/detalhes NomeDoNavio - Mostra os detalhes de um navio específico\n"
        "/ping - Debug\n"
        "/status - Mostra a última checagem, total de navios e navios previstos\n"
        
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# === COMANDO /detalhes ===
async def detalhes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retorna detalhes de um navio específico"""
    if not context.args:
        await update.message.reply_text("❗ Use assim: /detalhes NomeDoNavio")
        return

    nome = " ".join(context.args).lower()
    if nome in detalhes_navios:
        msg = formatar_detalhes(detalhes_navios[nome])
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Nenhum navio encontrado com esse nome.")

# === COMANDO /status ===
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra status do bot, última atualização e navios previstos"""
    if ultima_lista:
        ultima_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        total_navios = len(detalhes_navios)
        navios = "\n".join(f"🛳️ {m['nome']} | {m['tipo']} | Berço: {m['berco']}" 
                           for m in ultima_lista)
        msg = (
            f"🤖 *DAAS PortWatch Status*\n\n"
            f"📅 Última checagem: {ultima_atualizacao}\n"
            f"🔢 Total de navios monitorados: {total_navios}\n\n"
            f"*Navios previstos:*\n{navios}"
        )
    else:
        msg = "🤖 O bot ainda não realizou a primeira checagem do site."
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# === COMANDO /ping ===
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde se o bot está ativo"""
    await update.message.reply_text("Pong! Bot ativo ✅")

# === MAIN ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("detalhes", detalhes))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))

    async def loop_monitoramento():
        while True:
            await verificar_novidades(app)
            await asyncio.sleep(600)  # 10 minutos

    asyncio.create_task(loop_monitoramento())

    print("🤖 Bot DAAS PortWatch iniciado!")
    await app.run_polling()


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import asyncio
    # asyncio.run(main())