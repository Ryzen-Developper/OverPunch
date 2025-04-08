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

# Flask para manter o bot online e escutar o webhook
app = Flask(__name__)

# Variável de cache local
jogadores_online = 0

@app.route('/')
def home():
    return "Bot está rodando!"

@app.route('/webhook', methods=['POST'])
def webhook():
    print("📩 Webhook recebido: solicitando atualização da contagem de jogadores...")
    asyncio.run_coroutine_threadsafe(atualizar_jogadores(), bot.loop)
    return "Atualizado", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Inicia o servidor keep_alive
keep_alive()

# Carrega variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('TOKEN')

# IDs
UNIVERSE_ID = 7495593772
GUILD_ID = 1358529264349085849
CHANNEL_ID = 1358565119092723742

# Intents e bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
start_time = time.time()

# Função que atualiza o cache e status
async def atualizar_jogadores():
    global jogadores_online
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
                if response.status == 200:
                    data = await response.json()
                    jogadores_online = data['data'][0]['playing']

                    # Atualiza nome do canal
                    guild = bot.get_guild(GUILD_ID)
                    channel = guild.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.edit(name=f'〔🟢〕Active Counter: {jogadores_online}')

                    # Atualiza status do bot
                    await bot.change_presence(
                        activity=discord.Game(name=f"🎮 OverPunch 🥊🔥 | {jogadores_online} online"),
                        status=discord.Status.online
                    )

                    print(f"✅ Atualizado via webhook: {jogadores_online} jogadores online")
                else:
                    print(f"⚠️ Erro ao consultar API da Roblox: {response.status}")
        except Exception as e:
            print(f"❌ Erro durante atualização: {e}")

@bot.event
async def on_ready():
    await atualizar_jogadores()
    print(f'✅ Bot conectado como {bot.user}')

    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'✅ Comandos sincronizados: {len(synced)}')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

# ================= COMANDOS USANDO CACHE =====================
@tree.command(name="status", description="Veja o status atual do bot e jogadores online", guild=discord.Object(id=GUILD_ID))
async def status_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Status Atual",
        description=f"Atualmente, **{jogadores_online}** pessoas estão jogando OverPunch 🥊🔥.",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="jogo", description="Veja detalhes sobre o jogo OverPunch 🥊🔥", guild=discord.Object(id=GUILD_ID))
async def jogo_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📌 Informações do Jogo",
        description=f"**OverPunch 🥊🔥**\n[🔗 Acessar no Roblox](https://www.roblox.com/games/7495593772/OverPunch)",
        color=0xFFD700
    )
    embed.set_thumbnail(url="https://tr.rbxcdn.com/3f688f75e6b2dc47c9738cd6dca3fcdf/150/150/Image/Png")
    embed.add_field(name="👑 Dono", value="kaua23193", inline=True)
    embed.add_field(name="👥 Jogando agora", value=str(jogadores_online), inline=True)
    embed.set_footer(text="Powered by OverPunch")
    await interaction.response.send_message(embed=embed, ephemeral=False)

# Slash Command para jogar
@tree.command(name="jogar", description="Receba um botão para entrar no OverPunch 🥊🔥", guild=discord.Object(id=GUILD_ID))
async def jogar_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Jogue OverPunch 🥊🔥 agora!",
        description="Clique no botão abaixo para entrar no jogo no Roblox.",
        color=0x43B581
    )
    embed.set_thumbnail(url="https://tr.rbxcdn.com/3f688f75e6b2dc47c9738cd6dca3fcdf/150/150/Image/Png")
    embed.set_footer(text="Powered by OverPunch")

    view = discord.ui.View()
    button = discord.ui.Button(
        label="Entrar no OverPunch",
        url="https://www.roblox.com/games/7495593772/OverPunch"
    )
    view.add_item(button)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# Comando /ajuda
@tree.command(name="ajuda", description="Veja todos os comandos disponíveis", guild=discord.Object(id=GUILD_ID))
async def ajuda_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Lista de Comandos",
        description="Aqui estão os comandos disponíveis:",
        color=0x7289DA
    )
    embed.add_field(name="/jogar", value="Receba um botão para entrar no OverPunch 🥊🔥", inline=False)
    embed.add_field(name="/info", value="Mostra informações sobre o bot", inline=False)
    embed.add_field(name="/status", value="Veja o status atual do bot e jogadores online", inline=False)
    embed.add_field(name="/ping", value="Veja a latência do bot", inline=False)
    embed.add_field(name="/uptime", value="Veja há quanto tempo o bot está online", inline=False)
    embed.add_field(name="/jogo", value="Veja detalhes sobre o jogo OverPunch 🥊🔥", inline=False)
    embed.set_footer(text="Powered by OverPunch")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Comando /info
@tree.command(name="info", description="Mostra informações sobre o bot", guild=discord.Object(id=GUILD_ID))
async def info_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ Informações do Bot",
        description="Este bot mostra o número de jogadores ativos no OverPunch 🥊🔥 e muito mais.",
        color=0x5865F2
    )
    embed.add_field(name="Desenvolvedor", value="kauax2 (Discord) / kaua23193 (Roblox)", inline=True)
    embed.add_field(name="Jogo", value="[OverPunch 🥊🔥](https://www.roblox.com/games/7495593772/OverPunch)", inline=True)
    embed.set_footer(text="Feito com 💙 para a comunidade Roblox")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Comando /ping
@tree.command(name="ping", description="Veja a latência do bot", guild=discord.Object(id=GUILD_ID))
async def ping_command(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latência: {latency}ms', ephemeral=True)

# Comando /uptime
@tree.command(name="uptime", description="Veja há quanto tempo o bot está online", guild=discord.Object(id=GUILD_ID))
async def uptime_command(interaction: discord.Interaction):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    await interaction.response.send_message(f'🕒 Uptime: {uptime_str}', ephemeral=True)

bot.run(TOKEN)
