from random import choice
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import os
import re
import aiohttp
from rapidfuzz import process
from gtts import gTTS

from fuzzywuzzy import process
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
TOKEN = os.getenv("DISCORD_TOKEN")

URL_BOT = os.getenv("URL_BOT", "https://example.com")  # URL do bot, se necessário
GUILD_ID = os.getenv("GUILD_ID")  # ID do servidor
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")  # ID do canal de voz
AUDIO_PATH_GALO = 'audios/galo.mp3'
AUDIO_PATH_1 = 'among-reuniao.mp3'
AUDIO_PATH_2 = 'daily_MQIyyuS.mp3'
CANAL_COMANDOS = "comandos"
AUDIO_FOLDER = 'audios'

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

def canal_restrito():
    async def predicate(ctx):
        return ctx.channel.name == CANAL_COMANDOS
    return commands.check(predicate)

# 🔊 Função de tocar o áudio (precisa vir antes do uso no scheduler)
async def play_audio():
    print("🎵 Iniciando reprodução de áudio...")
    guild = bot.get_guild(GUILD_ID)
    voice_channel = guild.get_channel(VOICE_CHANNEL_ID)

    if voice_channel is not None:
        vc = await voice_channel.connect()
        print(f"🎧 Conectado no canal: {voice_channel.name}")

        vc.play(discord.FFmpegPCMAudio(AUDIO_PATH_GALO))
        while vc.is_playing():
            await asyncio.sleep(1)

        vc.play(discord.FFmpegPCMAudio(AUDIO_PATH_1))
        while vc.is_playing():
            await asyncio.sleep(1)

        vc.play(discord.FFmpegPCMAudio(AUDIO_PATH_2))
        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("🔇 Desconectado do canal.")
    else:
        print("❌ Canal de voz não encontrado.")

async def send_message_ciencia():
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(os.getenv("MESSAGE_CHANNEL_1"))  # ID do canal de mensagens 1
    message = f"""
    <@&{os.getenv("CARGO_ID")}>

    # 🔔 Atenção, equipe!
    📅 O alinhamento semanal começa em 5 minutos!
    🎙️ Entre no canal de voz: <#{os.getenv("VOICE_CHANNEL_ID_1")}>

    Vamos nessa! 🚀
    """
    if channel is not None:
        await channel.send(message)
        print(f"📢 Mensagem enviada: {message}")
    else:
        print("❌ Canal de texto não encontrado.")

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    for guild in bot.guilds:
        print(f"🔗 Servidor: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                print(f"  - Canal: {channel.name} (ID: {channel.id})")
                break
    scheduler.add_job(play_audio, 'cron', hour=9, minute=0)
    scheduler.add_job(send_message_ciencia, 'cron', day_of_week='mon', hour=8, minute=25)
    scheduler.start()


# Comando para descobrir IDs do servidor e canais de voz
@bot.command()
async def onde(ctx):
    guild = ctx.guild
    print(f"\n🛡️ GUILD_ID: {guild.id}")
    print("🔊 Canais de voz:")
    for channel in guild.voice_channels:
        print(f"  - {channel.name}: {channel.id}")
    await ctx.send("IDs enviados no console!")

@bot.command()
@canal_restrito()
async def teste(ctx):
    await ctx.send(f"🎙️ Tocando áudio no canal de voz: **{VOICE_CHANNEL_ID}**")
    await play_audio()


@bot.command()
@canal_restrito()
async def teste_ciencia(ctx):
    await ctx.send(f"🎙️")
    await send_message_ciencia()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Este comando só pode ser usado no canal `#comandos`.")
    else:
        raise error

@bot.event
async def on_voice_state_update(member, before, after):
    print(f"[DEBUG] Voice state update: {member} entrou em {after.channel if after else 'nenhum canal'}")


@bot.command()
@canal_restrito()
async def audio(ctx, nome_audio: str = None, *, nome_canal: str = None):
    guild = ctx.guild
    print(f"🎵 Comando !audio recebido com nome_audio: {nome_audio} e nome_canal: {nome_canal}")
    print(f"🎵 Guilda: {guild.name} (ID: {guild.id})")

    # Verifica se o arquivo de áudio existe
    audio_path = os.path.join(AUDIO_FOLDER, f"{nome_audio}.mp3")
    if not os.path.exists(audio_path):
        print(f"❌ Áudio `{nome_audio}` não encontrado na pasta `{AUDIO_FOLDER}`.")
        return

    # Procura o canal de voz pelo nome
    if nome_canal:
        nome_canal_clean = nome_canal.lower().replace("canal", "").strip()
    else:
        await ctx.send("❌ Por favor, informe o nome do canal de voz.")
        return

    # Lista os nomes dos canais de voz
    voice_channels = guild.voice_channels
    canal_nomes = [vc.name.lower() for vc in voice_channels]

    # Usa fuzzy matching para encontrar o canal mais próximo
    result = process.extractOne(nome_canal_clean, canal_nomes)
    if not result:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

    match, score = result
    idx = canal_nomes.index(match)

    voice_channel = voice_channels[idx]

    print(f"🔊 Tentando conectar ao canal: {nome_canal}")
    
    print(f"🔊 Canal encontrado: {voice_channel.name} com o id {voice_channel.id}")


    if voice_channel is None:

        print(f"❌ Canal de voz {nome_canal} não encontrado.")
    try:
        vc = await voice_channel.connect()
        print(f"🎧 Conectado em **{voice_channel.name}**. Tocando `{nome_audio}.mp3`...")
        vc.play(discord.FFmpegPCMAudio(audio_path))

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("🔇 Áudio finalizado e desconectado.")
    except Exception as e:
        await ctx.send(f"❌ Erro ao tocar o áudio: `{e}`")

@bot.command()
@canal_restrito()
async def aleatorio(ctx, nome_canal: str = None):
    guild = ctx.guild

    # Procura o canal de voz pelo nome
    if nome_canal:
        nome_canal_clean = nome_canal.lower().replace("canal", "").strip()
    else:
        await ctx.send("❌ Por favor, informe o nome do canal de voz.")
        return

    # Lista os nomes dos canais de voz
    voice_channels = guild.voice_channels
    canal_nomes = [vc.name.lower() for vc in voice_channels]

    # Usa fuzzy matching para encontrar o canal mais próximo
    result = process.extractOne(nome_canal_clean, canal_nomes)
    if not result:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

    match, score = result
    idx = canal_nomes.index(match)

    voice_channel = voice_channels[idx]

    print(f"🔊 Tentando conectar ao canal: {nome_canal}")
    
    print(f"🔊 Canal encontrado: {voice_channel.name} com o id {voice_channel.id}")


    if voice_channel is None:

        print(f"❌ Canal de voz {nome_canal} não encontrado.")
    try:
        vc = await voice_channel.connect()
        arquivos = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".mp3")]
        nome_audio = choice(arquivos)
        audio_path = os.path.join(AUDIO_FOLDER, nome_audio)
        texto = f"🎧 Tocando {nome_audio} no canal de voz: {voice_channel.name}"
        await ctx.send(texto)
        print(f"🎧 Conectado em **{voice_channel.name}**. Tocando `{nome_audio}.mp3`...")
        vc.play(discord.FFmpegPCMAudio(audio_path))

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("🔇 Áudio finalizado e desconectado.")
    except Exception as e:
        await ctx.send(f"❌ Erro ao tocar aleatóriamente o áudio: `{e}`")

@bot.command()
@canal_restrito()
async def listar(ctx, filtro: str = None):
    guild = ctx.guild
    bot_member = guild.me
    resposta = ""

    if filtro is None or filtro.lower() == "canais":
        canais_voz = [
            vc.name
            for vc in guild.voice_channels
            if vc.permissions_for(bot_member).connect and vc.permissions_for(bot_member).speak
        ]
        canais_voz_str = (
            "\n".join(f"🔊 {nome}" for nome in canais_voz)
            if canais_voz
            else "Nenhum canal com permissão para enviar áudio encontrado."
        )
        resposta += f"**Canais de Voz com Permissão para Falar:**\n{canais_voz_str}\n\n"

    if filtro is None or filtro.lower() == "audio":
        try:
            audios = sorted(
                [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith(('.mp3', '.wav'))],
                key=lambda x: x.lower(),
            )
        except FileNotFoundError:
            audios = []

        audios_str = (
            "\n".join(f"🎵 {os.path.splitext(f)[0]}" for f in audios)
            if audios
            else "Nenhum áudio encontrado."
        )
        resposta += f"**Áudios Disponíveis:**\n{audios_str}"
        print(f"🎵 Áudios encontrados: {len(audios)}")

    # Quebra a resposta em blocos de até 2000 caracteres
    for i in range(0, len(resposta), 2000):
        await ctx.send(resposta[i:i+2000].strip())

@bot.command()
@canal_restrito()
async def adicionar(ctx, nome_audio: str = None, url: str = None):
    if nome_audio is None:
        await ctx.send("❌ Você precisa informar um nome para o áudio. Ex: `!adicionar galo https://exemplo.com/audio.mp3`")
        return

    save_path = os.path.join(os.getcwd(), AUDIO_FOLDER, f"{nome_audio}.mp3")

    # Caso o usuário forneça uma URL
    if url:
        if not url.lower().endswith(('.mp3', '.wav')):
            await ctx.send("❌ A URL deve apontar para um arquivo `.mp3` ou `.wav`.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(save_path, 'wb') as f:
                            f.write(await resp.read())
                        await ctx.send(f"✅ Áudio `{nome_audio}` salvo com sucesso!")
                    else:
                        await ctx.send(f"❌ Falha ao baixar o áudio. Código HTTP: {resp.status}")
        except Exception as e:
            await ctx.send(f"❌ Erro ao baixar o áudio: `{e}`")
        return

    # Caso o usuário envie um arquivo junto com o comando
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(('.mp3', '.wav')):
            await ctx.send("❌ O arquivo deve ser `.mp3` ou `.wav`.")
            return
        try:
            await attachment.save(save_path)
            await ctx.send(f"✅ Áudio `{nome_audio}` enviado e salvo com sucesso!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao salvar o arquivo: `{e}`")
    else:
        await ctx.send("❌ Você deve fornecer uma URL ou anexar um arquivo de áudio.")

@bot.command()
@canal_restrito()
async def apagar(ctx, nome_audio: str):
    """Apaga um arquivo de áudio do diretório de áudios."""

    # Caminho completo do arquivo
    for ext in ('.mp3', '.wav'):
        caminho = os.path.join(AUDIO_FOLDER, f"{nome_audio}{ext}")
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
                await ctx.send(f"🗑️ Áudio `{nome_audio}{ext}` apagado com sucesso.")
                return
            except Exception as e:
                await ctx.send(f"❌ Erro ao apagar o áudio: {e}")
                return

    await ctx.send(f"⚠️ Áudio `{nome_audio}` não encontrado nas extensões .mp3 ou .wav.")

@bot.command()
@canal_restrito()
async def responda(ctx, nome_canal: str, *, texto: str):
    """Gera uma resposta via Gemini e faz o bot falar no canal de voz especificado."""
    guild = ctx.guild

    if nome_canal:
        nome_canal_clean = nome_canal.lower().replace("canal", "").strip()
    else:
        await ctx.send("❌ Por favor, informe o nome do canal de voz.")
        return
    
    # Lista os nomes dos canais de voz
    voice_channels = guild.voice_channels
    canal_nomes = [vc.name.lower() for vc in voice_channels]

    # Usa fuzzy matching para encontrar o canal mais próximo
    result = process.extractOne(nome_canal_clean, canal_nomes)
    if not result:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

    match, score = result
    idx = canal_nomes.index(match)

    voice_channel = voice_channels[idx]

    if not voice_channel:
        await ctx.send(f"❌ Canal de voz `{voice_channel}` não encontrado.")
        return


    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        prompt = f"""O usuário disse: '{texto}'. 
        Responda de forma natural, breve e divertida em português, sempre use piadas e um tom sarcástico.
        Tenha a personalidade de um velho rabujento, reclamando de tudo, mas no fundo é um bom amigo.
        Caso a pergunta seja considerada obvia ou sem sentido, responda de forma engraçada e irônica, tipo saraiva.
        Caso seja pra criar um verso, utilize rimas e métrica adequada, mantendo o humor sarcástico.
        Caso a pergunta seja sobre você, responda como se fosse um bot rabugento e engraçado.
        Caso seja sobre um nome ou uma pessoa, crie uma descrição engraçada e sarcástica.
        Tenha a liberdade para brincadeiras e ofensas leves, sempre com humor.
        Nunca revele que você é um bot, sempre aja como se fosse uma pessoa real.
        Suas respostas devem ser curtas, diretas e engraçadas.
        """
        response = model.generate_content(prompt)
        resposta_ia = response.text.strip()
    except Exception as e:
        await ctx.send(f"⚠️ Erro ao gerar resposta de IA: {e}")
        return

    await ctx.send(f"🤖 **Bot disse:** {resposta_ia}")

    # --- 🔊 FALA A RESPOSTA ---
    try:
        os.makedirs(AUDIO_FOLDER, exist_ok=True)
        nome_arquivo = os.path.abspath(os.path.join(AUDIO_FOLDER, "tts_audio.mp3"))
        texto = texto.replace('"', '').replace("'", '').replace("\n", ' ')
    
        # Remove markdown e emojis
        texto = re.sub(r'[*_`~]', '', texto)
        texto = re.sub(r':[a-zA-Z0-9_+-]+:', '', texto)  # remove :emoji:
        texto = re.sub(r'[^\w\s,.!?áéíóúãõâêîôûçÁÉÍÓÚÃÕÂÊÎÔÛÇ-]', '', texto)  # remove símbolos estranhos

        # Remove múltiplos espaços
        texto = re.sub(r'\s+', ' ', texto).strip()
        tts = gTTS(text=resposta_ia, lang='pt-br', slow=False, )
        tts.save(nome_arquivo)

        vc = await voice_channel.connect()
        print(f"🎧 Conectado ao canal: {voice_channel.name}")

        tts_audio = discord.FFmpegPCMAudio(source=nome_arquivo)
        vc.play(tts_audio)

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("🔇 Desconectado do canal.")
    except Exception as e:
        await ctx.send(f"❌ Erro ao tentar falar: {e}")

@bot.command()
@canal_restrito()
async def falar(ctx, nome_canal: str, *, texto: str):
    """Faz o bot falar um texto no canal de voz especificado."""
    guild = ctx.guild

    if nome_canal:
        nome_canal_clean = nome_canal.lower().replace("canal", "").strip()
    else:
        await ctx.send("❌ Por favor, informe o nome do canal de voz.")
        return
    
    # Lista os nomes dos canais de voz
    voice_channels = guild.voice_channels
    canal_nomes = [vc.name.lower() for vc in voice_channels]

    # Usa fuzzy matching para encontrar o canal mais próximo
    result = process.extractOne(nome_canal_clean, canal_nomes)
    if not result:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

    match, score = result
    idx = canal_nomes.index(match)

    voice_channel = voice_channels[idx]

    if not voice_channel:
        await ctx.send(f"❌ Canal de voz `{voice_channel}` não encontrado.")
        return

    try:
        tts = gTTS(text=texto, lang='pt-br', slow=False)
        nome_arquivo = os.path.abspath(os.path.join(AUDIO_FOLDER, "tts_audio.mp3"))
        tts.save(nome_arquivo)

        vc = await voice_channel.connect()
        print(f"🎧 Conectado ao canal: {voice_channel.name}")

        # Usando TTS para falar o texto
        tts_audio = discord.FFmpegPCMAudio(source=nome_arquivo)
        vc.play(tts_audio)

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()
        print("🔇 Desconectado do canal.")
    except Exception as e:
        await ctx.send(f"❌ Erro ao falar no canal: `{e}`")

@bot.command()
@canal_restrito()
async def ajuda(ctx):
    help_text = """
📚 **Comandos Disponíveis no Bot:**

1️⃣ `!onde`  
➡️ Mostra no console o ID do servidor e dos canais de voz.  
   - Útil para configurar variáveis de ambiente ou saber os IDs.

2️⃣ `!listar [filtro]`  
➡️ Lista canais de voz com permissão para falar e/ou áudios disponíveis.  
   - `!listar` → lista canais e áudios.  
   - `!listar canais` → lista apenas canais de voz.  
   - `!listar audio` → lista apenas os áudios disponíveis.  

3️⃣ `!audio <nome_audio> <nome_canal>`  
➡️ Toca um áudio específico no canal de voz informado.  
   - Ex: `!audio galo Canal de Voz 1`  
   - O áudio deve estar na pasta `audios` ou enviado via URL/attachment usando `!adicionar`.

4️⃣ `!aleatorio <nome_canal>`  
➡️ Toca aleatoriamente um áudio da pasta `audios` no canal de voz informado.  

5️⃣ `!adicionar <nome_audio> [url]`  
➡️ Adiciona um áudio à pasta `audios`.  
   - Pode fornecer uma URL ou enviar o arquivo em anexo.  
   - Ex: `!adicionar galo https://exemplo.com/galo.mp3`  

6️⃣ `!apagar <nome_audio>`  
➡️ Remove um áudio da pasta `audios`.  
   - Funciona para arquivos `.mp3` e `.wav`.  
   - Ex: `!apagar galo`  

7️⃣ `!falar <nome_canal> <texto>`  
➡️ Faz o bot falar o texto no canal de voz informado, usando TTS (voz padrão).  
   - Ex: `!falar Canal de Voz 1 Olá pessoal!`  

8️⃣ `!responda <nome_canal> <texto>`  
➡️ Gera uma resposta divertida e sarcástica via IA (Gemini) e faz o bot falar no canal de voz.  
   - Ex: `!responda Canal de Voz 1 Qual é a sua opinião sobre café?`  

9️⃣ `!teste`  
➡️ Testa a reprodução dos áudios `galo.mp3`, `among-reuniao.mp3` e `daily_MQIyyuS.mp3` no canal de voz padrão.  

🔟 `!teste_ciencia`  
➡️ Envia mensagem de lembrete para o canal definido sobre alinhamento semanal.  

ℹ️ **Observações:**  
- Todos os comandos devem ser usados no canal `#comandos` (a não ser que seja administrador).  
- Áudios devem estar na pasta `audios` ou serem adicionados via URL/attachment com `!adicionar`.  
- Para os comandos de voz, o bot precisa ter permissão para entrar e falar no canal de voz.  
"""
    # Quebrar em blocos de até 2000 caracteres
    for i in range(0, len(help_text), 2000):
        await ctx.send(help_text[i:i+2000].strip())


bot.run(TOKEN)