# 🤖 Bot do Discord - Alinhamento Semanal & Áudios Personalizados

Este bot do Discord foi criado para:
- Reproduzir áudios no canal de voz em horários agendados.
- Enviar mensagens automáticas para organização de reuniões.
- Permitir comandos de gerenciamento e reprodução de áudios personalizados.
- Utilizar TTS (texto para fala) em português com `gTTS`.

---

## 🧰 Tecnologias Utilizadas

- [discord.py](https://discordpy.readthedocs.io/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [aiohttp](https://docs.aiohttp.org/)
- [rapidfuzz](https://maxbachmann.github.io/RapidFuzz/)
- [gTTS (Google Text-to-Speech)](https://pypi.org/project/gTTS/)
- [FFmpeg](https://ffmpeg.org/) (para reprodução de áudio)

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/thomazdevmaster/bot-discord.git
cd bot-discord
```
### 2. Crie um ambiente virtual (opcional, mas recomendado)

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. Instale as dependências

```bash
pip install -r requirements.txt

sudo apt install ffmpeg
```
⚙️ Configuração
Crie um arquivo .env com os seguintes valores:

```bash
DISCORD_TOKEN=seu_token_do_discord
GUILD_ID=123456789012345678               # ID do servidor
VOICE_CHANNEL_ID=123456789012345678       # Canal de voz padrão para o áudio agendado
VOICE_CHANNEL_ID_1=123456789012345678     # Canal de voz para a mensagem semanal
MESSAGE_CHANNEL_1=123456789012345678      # Canal de texto para a mensagem semanal
CARGO_ID=123456789012345678               # ID do cargo a ser mencionado (ex: equipe)
GOOGLE_API_KEY=123456789                  # Chave da API do Google
```

▶️ Executando o Bot

```bash
python bot.py
```

📁 Estrutura Esperada
```bash
Copiar
Editar
bot-discord/
├── audios/
│   ├── galo.mp3
│   ├── among-reuniao.mp3
│   ├── daily_MQIyyuS.mp3
├── bot.py
├── .env
├── requirements.txt
🔐 Segurança
```

⚠️ Nunca comite o arquivo .env nem tokens do bot.

O GitHub pode bloquear seu push se detectar segredos nos commits.
Use variáveis de ambiente ou arquivos ignorados com .gitignore.

🧠 Créditos e Referências
Criado por @thomazdevmaster
Baseado em práticas modernas de bots com Discord e Python.



