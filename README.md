# 🤖 DAAS PortWatch Bot

O **DAAS PortWatch** é um bot do Telegram que monitora manobras de navios no porto e envia alertas automáticos quando novas informações são detectadas.

---

## 📌 Funcionalidades

- Monitora navios previstos no porto.
- Alertas automáticos quando surgem novas manobras.
- Comando `/detalhes` para ver informações completas de um navio específico.
- Comando `/ping` para testar se o bot está online.
- Comando `/status` para conferir o status atual e os navios previstos.

---

## 🛠️ Comandos disponíveis

| Comando       | Descrição                                        |
|---------------|--------------------------------------------------|
| `/detalhes`   | Retorna detalhes completos de um navio           |
| `/ping`       | Retorna "pong" para testar se o bot está ativo   |
| `/status`     | Mostra a última checagem e navios previstos      |

---

## ⚙️ Configuração

```bash

#1. Clone o repositório:
git clone https://github.com/brvnx/DAAS-PortWatch-Bot.git

#2. Instale dependências:
pip install -r requirements.txt

#3. Crie um arquivo .env com suas credenciais do Telegram:
TOKEN=seu_token_aqui
CHAT_ID=seu_chatid_aqui
URL=http://www.apem-ma.com.br/index.php?module=shipmaneuvering

#4. Execute o bot:
python bot_daas.py