import discord
from discord.ext import tasks, commands
from discord import app_commands
import aiohttp
import asyncio
import os
import time
from dotenv import load_dotenv
from flask import Flask, request
from threading import Thread

# ========== FLASK SETUP ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando!"

# WEBHOOK DO ROBLOX
@app.route('/webhook', methods=['POST'])
def webhook():
    print("✅ Webhook recebido!")

    if bot.is_closed() or not bot.is_ready():
        print("⚠️ Bot ainda não está pronto ou está fechado.")
        return "Bot não pronto.", 503
    
        try:
            future = asyncio.run_coroutine_threadsafe(verificar_e_atualizar(), bot.loop)
            future.result(timeout=10)
            print("✅ Atualização disparada com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao tentar atualizar: {e}")
    else:
        print("⚠️ Bot ainda não está pronto.")

    return "Webhook processado.", 200

# Função de verificação e atualização
async def verificar_e_atualizar():
    print("🛠️ Função verificar_e_atualizar foi chamada.")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                print("📥 Dados recebidos da API:", data)
                
                jogando_agora = data['data'][0]['playing']
                print(f"🔄 Jogadores online: {jogando_agora}")

                guild = bot.get_guild(GUILD_ID)
                channel = guild.get_channel(CHANNEL_ID)
                if channel:
                    await channel.edit(name=f'〔🟢〕Active Counter: {jogando_agora}')
                    print("✅ Canal atualizado com sucesso.")
                else:
                    print("❌ Canal não encontrado!")

                await bot.change_presence(
                    activity=discord.Game(name=f"🎮 OverPunch 🥊🔥 | {jogando_agora} online"),
                    status=discord.Status.online
                )
                print("✅ Status atualizado.")
            else:
                print(f"❌ Erro ao buscar dados na API do Roblox: {response.status}")

# ========== THREAD PARA FLASK ==========
def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ========== BOT DISCORD SETUP ==========
load_dotenv()
TOKEN = os.getenv('TOKEN')

UNIVERSE_ID = 7495593772
GUILD_ID = 1358529264349085849
CHANNEL_ID = 1358565119092723742

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
start_time = time.time()

@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)
    print(f"🔎 Servidor: {guild.name if guild else 'não encontrado'}")
    print(f"🔎 Canal: {channel.name if channel else 'não encontrado'}")
    
    await bot.change_presence(
        activity=discord.Game(name="🎮 OverPunch 🥊🔥"),
        status=discord.Status.online
    )
    print(f'✅ Bot conectado como {bot.user}')
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'✅ Comandos sincronizados: {len(synced)}')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

# ========== COMANDOS ==========
# Comandos de administração (/kick, /ban, /clear, /banlist)
# Comandos de interação (/jogar, /ajuda, /info, /status, /ping, /uptime, /jogo)

# --- Admin ---
@tree.command(name="kick", description="Expulsa um usuário do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Usuário para expulsar", motivo="Motivo da expulsão")
async def kick_command(interaction, user: discord.Member, motivo: str = "Não especificado"):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    await user.kick(reason=motivo)
    await interaction.response.send_message(f"👢 {user.name} foi expulso. Motivo: {motivo}")

@tree.command(name="ban", description="Bane um usuário do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Usuário para banir", motivo="Motivo do banimento")
async def ban_command(interaction, user: discord.Member, motivo: str = "Não especificado"):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    await user.ban(reason=motivo)
    await interaction.response.send_message(f"🔨 {user.name} foi banido. Motivo: {motivo}")

@tree.command(name="clear", description="Apaga mensagens do canal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(quantidade="Quantidade de mensagens (máx 100)")
async def clear_command(interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    if quantidade > 100:
        return await interaction.response.send_message("⚠️ Máximo de 100 mensagens.", ephemeral=True)
    await interaction.channel.purge(limit=quantidade)
    await interaction.response.send_message(f"🧹 {quantidade} mensagens apagadas.", ephemeral=True)

@tree.command(name="banlist", description="Lista de banidos", guild=discord.Object(id=GUILD_ID))
async def banlist_command(interaction):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
    bans = await interaction.guild.bans()
    if not bans:
        return await interaction.response.send_message("✅ Nenhum banido.", ephemeral=True)
    nomes = [f"{ban.user.name}#{ban.user.discriminator}" for ban in bans]
    await interaction.response.send_message("🔨 Banidos:\n" + "\n".join(nomes), ephemeral=True)

# --- Interação ---
@tree.command(name="jogar", description="Botão para entrar no OverPunch 🥊🔥", guild=discord.Object(id=GUILD_ID))
async def jogar_command(interaction):
    embed = discord.Embed(
        title="🎮 Jogue OverPunch 🥊🔥 agora!",
        description="Clique no botão abaixo para entrar no jogo no Roblox.",
        color=0x43B581
    )
    embed.set_thumbnail(url="https://tr.rbxcdn.com/3f688f75e6b2dc47c9738cd6dca3fcdf/150/150/Image/Png")
    embed.set_footer(text="Powered by OverPunch")

    view = discord.ui.View()
    button = discord.ui.Button(label="Entrar no OverPunch", url="https://www.roblox.com/games/7495593772/OverPunch")
    view.add_item(button)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="ajuda", description="Lista de comandos", guild=discord.Object(id=GUILD_ID))
async def ajuda_command(interaction):
    embed = discord.Embed(
        title="📖 Comandos disponíveis",
        description="Aqui estão os comandos que você pode usar:",
        color=0x7289DA
    )
    comandos = {
        "/jogar": "Entrar no OverPunch 🥊🔥",
        "/info": "Informações do bot",
        "/status": "Status e jogadores online",
        "/ping": "Latência do bot",
        "/uptime": "Tempo online do bot",
        "/jogo": "Informações do jogo",
    }
    for cmd, desc in comandos.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="info", description="Info do bot", guild=discord.Object(id=GUILD_ID))
async def info_command(interaction):
    embed = discord.Embed(
        title="ℹ️ Sobre o bot",
        description="Bot oficial do OverPunch 🥊🔥.",
        color=0x5865F2
    )
    embed.add_field(name="Dev", value="kauax2 / kaua23193", inline=True)
    embed.add_field(name="Jogo", value="[OverPunch 🥊🔥](https://www.roblox.com/games/7495593772/OverPunch)", inline=True)
    embed.set_footer(text="Feito com 💙 para a comunidade Roblox")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="status", description="Status e jogadores online", guild=discord.Object(id=GUILD_ID))
async def status_command(interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                jogando_agora = data['data'][0]['playing']
                embed = discord.Embed(
                    title="📊 Status Atual",
                    description=f"**{jogando_agora}** jogadores online no OverPunch 🥊🔥",
                    color=0x00FF00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Erro ao obter status.", ephemeral=True)

@tree.command(name="ping", description="Latência do bot", guild=discord.Object(id=GUILD_ID))
async def ping_command(interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latência: {latency}ms', ephemeral=True)

@tree.command(name="uptime", description="Tempo online do bot", guild=discord.Object(id=GUILD_ID))
async def uptime_command(interaction):
    uptime = int(time.time() - start_time)
    h, m = divmod(uptime, 3600)
    m, s = divmod(m, 60)
    await interaction.response.send_message(f'🕒 Uptime: {h}h {m}m {s}s', ephemeral=True)

@tree.command(name="jogo", description="Informações do jogo", guild=discord.Object(id=GUILD_ID))
async def jogo_command(interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                jogo = data['data'][0]
                embed = discord.Embed(
                    title="📌 OverPunch 🥊🔥",
                    description=f"[🔗 Ver no Roblox](https://www.roblox.com/games/7495593772/OverPunch)",
                    color=0xFFD700
                )
                embed.set_thumbnail(url=jogo.get("thumbnails", [{}])[0].get("imageUrl", "https://tr.rbxcdn.com/3f688f75e6b2dc47c9738cd6dca3fcdf/150/150/Image/Png"))
                embed.add_field(name="👑 Dono", value="kaua23193", inline=True)
                embed.add_field(name="👥 Jogando agora", value=str(jogo['playing']), inline=True)
                embed.set_footer(text="Powered by OverPunch")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Erro ao buscar dados do jogo.", ephemeral=True)

# ========== INICIA O BOT ==========
bot.run(TOKEN)
