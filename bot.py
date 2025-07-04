import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import os
import aiohttp
from rapidfuzz import process
from gtts import gTTS

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


@bot.command()
@canal_restrito()
async def audio(ctx, nome_audio: str = None, *, nome_canal: str = None):
    guild = bot.get_guild(GUILD_ID)

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
    match, score, idx = process.extractOne(nome_canal_clean, canal_nomes)

    if score < 70:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

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
async def listar(ctx, filtro: str = None):
    guild = ctx.guild
    bot_member = guild.me

    resposta = ""

    if filtro is None or filtro.lower() == "canais":
        canais_voz = []
        for vc in guild.voice_channels:
            perms = vc.permissions_for(bot_member)
            if perms.connect and perms.speak:
                canais_voz.append(vc.name)

        canais_voz_str = "\n".join(f"🔊 {nome}" for nome in canais_voz) if canais_voz else "Nenhum canal com permissão para enviar áudio encontrado."
        resposta += f"**Canais de Voz com Permissão para Falar:**\n{canais_voz_str}\n\n"

    if filtro is None or filtro.lower() == "audio":
        # Lista os arquivos de áudio
        try:
            audios = sorted(
            [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith(('.mp3', '.wav'))],
            key=lambda x: x.lower()  # Ordenação case-insensitive
        )
        except FileNotFoundError:
            audios = []
        audios_str = "\n".join(f"🎵 {os.path.splitext(f)[0]}" for f in audios) if audios else "Nenhum áudio encontrado."
        resposta += f"**Áudios Disponíveis:**\n{audios_str}"

    await ctx.send(resposta.strip())

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
    match, score, idx = process.extractOne(nome_canal_clean, canal_nomes)

    if score < 70:
        await ctx.send(f"❌ Nenhum canal de voz encontrado com nome semelhante a `{nome_canal}`.")
        return

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
📚 **Comandos Disponíveis:**

`!help`
➡️ Mostra esta lista de comandos.

`!onde`
➡️ Mostra os IDs do servidor e canais de voz no console.

`!listar [filtro]`
➡️ Lista canais de voz com permissão para falar e/ou áudios disponíveis.
   - Ex: `!listar`
   - Ex: `!listar canais`
   - Ex: `!listar audio`

`!audio <nome_audio> <nome_canal>`
➡️ Toca um áudio no canal de voz especificado.
   - Ex: `!audio galo Canal de Voz 1`

    """
    await ctx.send(help_text)

bot.run(TOKEN)