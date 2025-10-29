import asyncio
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
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Alterado para padrão mais comum
CHAT_ID = os.getenv("CHAT_ID")
URL = os.getenv("URL")

# Verifica se as variáveis de ambiente estão carregadas
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN não encontrado nas variáveis de ambiente!")
if not CHAT_ID:
    raise ValueError("❌ CHAT_ID não encontrado nas variáveis de ambiente!")
if not URL:
    raise ValueError("❌ URL não encontrado nas variáveis de ambiente!")

print("✅ Variáveis de ambiente carregadas:")
print(f"   TOKEN: {TOKEN[:10]}...")
print(f"   CHAT_ID: {CHAT_ID}")
print(f"   URL: {URL}")

ultima_lista = []
detalhes_navios = {}

# === FUNÇÕES DE SCRAPING ===
def obter_manobras():
    """Lê a tabela de manobras e retorna lista de dicionários"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resposta = requests.get(URL, headers=headers, timeout=30)
        resposta.encoding = "utf-8"
        resposta.raise_for_status()  # Levanta exceção para erros HTTP
        
        soup = BeautifulSoup(resposta.text, "html.parser")

        tabela = soup.find("table")
        if not tabela:
            print("❌ Nenhuma tabela encontrada no site")
            return []

        linhas = tabela.find_all("tr")[1:]  # Pula o cabeçalho
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
        
        print(f"✅ {len(manobras)} manobras obtidas do site")
        return manobras
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao acessar o site: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro inesperado no scraping: {e}")
        return []

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
        print("🔍 Verificando novidades no site...")
        atual = obter_manobras()
        
        if not atual:
            print("⚠️ Nenhuma manobra obtida do site")
            return

        if not ultima_lista:
            # Primeira execução
            ultima_lista = atual
            detalhes_navios = {m["nome"].lower(): m for m in atual}
            print(f"✅ Primeira checagem concluída. {len(atual)} manobras encontradas.")
            return

        # Encontrar novas manobras
        novos = [m for m in atual if m not in ultima_lista]
        
        if novos:
            print(f"🎯 {len(novos)} novas manobras detectadas!")
            for m in novos:
                # Adiciona aos detalhes
                detalhes_navios[m["nome"].lower()] = m
                
                # Envia alerta
                msg = formatar_alerta(m)
                await app.bot.send_message(
                    chat_id=int(CHAT_ID), 
                    text=msg, 
                    parse_mode="Markdown"
                )
                print(f"📤 Alert enviado para: {m['nome']}")
                
                # Pequeno delay entre mensagens
                await asyncio.sleep(1)
            
            # Atualiza a lista de referência
            ultima_lista = atual
        else:
            print("✅ Nenhuma novidade encontrada.")
            
    except Exception as e:
        print(f"❌ Erro ao verificar site: {e}")

# === COMANDOS DO BOT ===
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

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra status do bot, última atualização e navios previstos"""
    if ultima_lista:
        ultima_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        total_navios = len(detalhes_navios)
        navios = "\n".join(f"🛳️ {m['nome']} | {m['tipo']} | Berço: {m['berco']}" 
                           for m in ultima_lista[:10])  # Limita a 10 para não ficar muito longo
        
        msg = (
            f"🤖 *DAAS PortWatch Status*\n\n"
            f"📅 Última checagem: {ultima_atualizacao}\n"
            f"🔢 Total de navios monitorados: {total_navios}\n\n"
            f"*Últimos navios previstos:*\n{navios}"
        )
    else:
        msg = "🤖 O bot ainda não realizou a primeira checagem do site."
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde se o bot está ativo"""
    await update.message.reply_text("Pong! Bot ativo ✅")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de início"""
    msg = (
        "🤖 *Bem-vindo ao DAAS PortWatch Bot!*\n\n"
        "Este bot monitora manobras de navios automaticamente.\n\n"
        "Use /help para ver todos os comandos disponíveis."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# === TAREFA EM SEGUNDO PLANO ===
async def background_monitor(app):
    """Tarefa de monitoramento em segundo plano"""
    while True:
        try:
            await verificar_novidades(app)
            await asyncio.sleep(600)  # 10 minutos
        except Exception as e:
            print(f"❌ Erro no monitoramento em background: {e}")
            await asyncio.sleep(60)  # Espera 1 minuto antes de tentar novamente

# === MAIN ===
async def main():
    """Função principal corrigida para Railway"""
    try:
        print("🚀 Iniciando DAAS PortWatch Bot...")
        
        # Cria a aplicação
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Adiciona handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("detalhes", detalhes))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("ping", ping))
        
        # Inicia a tarefa de monitoramento em background
        asyncio.create_task(background_monitor(app))
        
        print("✅ Bot inicializado com sucesso!")
        print("📡 Iniciando polling...")
        
        # Inicia o bot
        await app.run_polling()
        
    except Exception as e:
        print(f"❌ Erro fatal na inicialização: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"💥 Erro crítico: {e}")