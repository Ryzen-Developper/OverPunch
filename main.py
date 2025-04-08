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
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)

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

# ================= COMANDOS =====================
@tree.command(name="status", description="Veja o status atual do bot e jogadores online", guild=discord.Object(id=GUILD_ID))
async def status_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    embed = discord.Embed(
        title="📊 Status Atual",
        description=f"Atualmente, **{jogadores_online}** pessoas estão jogando OverPunch 🥊🔥.",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="jogo", description="Veja detalhes sobre o jogo OverPunch 🥊🔥", guild=discord.Object(id=GUILD_ID))
async def jogo_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
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

@tree.command(name="ajuda", description="Veja todos os comandos disponíveis", guild=discord.Object(id=GUILD_ID))
async def ajuda_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    embed = discord.Embed(title="📚 Comandos Disponíveis", color=0x3498db)
    embed.add_field(name="/status", value="Mostra quantos jogadores estão online no momento.", inline=False)
    embed.add_field(name="/jogo", value="Exibe informações sobre o jogo OverPunch.", inline=False)
    embed.add_field(name="/info", value="Mostra informações sobre o bot.", inline=False)
    embed.add_field(name="/ping", value="Mostra a latência do bot.", inline=False)
    embed.add_field(name="/uptime", value="Mostra há quanto tempo o bot está online.", inline=False)
    embed.add_field(name="/kick", value="Expulsa um usuário do servidor (admin).", inline=False)
    embed.add_field(name="/ban", value="Bane um usuário do servidor (admin).", inline=False)
    embed.add_field(name="/clear", value="Limpa mensagens no canal (admin).", inline=False)
    embed.add_field(name="/banlist", value="Mostra a lista de banidos (admin).", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="info", description="Veja informações sobre o bot", guild=discord.Object(id=GUILD_ID))
async def info_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    embed = discord.Embed(title="🤖 Informações do Bot", color=0x7289da)
    embed.add_field(name="Criador", value="kaua23193", inline=True)
    embed.add_field(name="Linguagem", value="Python 🐍", inline=True)
    embed.set_footer(text="Feito para o OverPunch 🥊🔥")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="ping", description="Veja o ping do bot", guild=discord.Object(id=GUILD_ID))
async def ping_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latência: {latency}ms", ephemeral=True)

@tree.command(name="uptime", description="Veja há quanto tempo o bot está online", guild=discord.Object(id=GUILD_ID))
async def uptime_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
    await interaction.response.send_message(f"⏱️ Uptime: {uptime_str}", ephemeral=True)

# ================= COMANDOS ADMINISTRATIVOS =====================
@tree.command(name="kick", description="Expulse um membro do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(kick_members=True)
async def kick_command(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado"):
    if interaction.response.is_done(): return
    await membro.kick(reason=motivo)
    await interaction.response.send_message(f"✅ {membro.mention} foi expulso. Motivo: {motivo}", ephemeral=True)

@tree.command(name="ban", description="Bane um membro do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(ban_members=True)
async def ban_command(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado"):
    if interaction.response.is_done(): return
    await membro.ban(reason=motivo)
    await interaction.response.send_message(f"🚫 {membro.mention} foi banido. Motivo: {motivo}", ephemeral=True)

@tree.command(name="clear", description="Limpa mensagens do canal", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_command(interaction: discord.Interaction, quantidade: int):
    if interaction.response.is_done(): return
    await interaction.channel.purge(limit=quantidade)
    await interaction.response.send_message(f"🧹 {quantidade} mensagens foram apagadas.", ephemeral=True)

@tree.command(name="banlist", description="Mostra a lista de banidos", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(ban_members=True)
async def banlist_command(interaction: discord.Interaction):
    if interaction.response.is_done(): return
    banidos = await interaction.guild.bans()
    if not banidos:
        await interaction.response.send_message("📜 Nenhum usuário banido.", ephemeral=True)
    else:
        lista = "\n".join([f"{ban.user.name}#{ban.user.discriminator}" for ban in banidos])
        await interaction.response.send_message(f"📜 Lista de banidos:\n{lista}", ephemeral=True)

bot.run(TOKEN)
