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

# Flask para manter o bot online
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando!"

# ROTA DE WEBHOOK DO ROBLOX
@app.route('/webhook', methods=['POST'])
def webhook():
    asyncio.run_coroutine_threadsafe(verificar_e_atualizar(), bot.loop)
    return "Webhook recebido!", 200

async def verificar_e_atualizar():
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                jogando_agora = data['data'][0]['playing']

                guild = bot.get_guild(GUILD_ID)
                channel = guild.get_channel(CHANNEL_ID)
                if channel:
                    await channel.edit(name=f'〔🟢〕Active Counter: {jogando_agora}')

                await bot.change_presence(
                    activity=discord.Game(name=f"🎮 OverPunch 🥊🔥 | {jogando_agora} online"),
                    status=discord.Status.online
                )

# Thread do Flask

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

cooldown_delay = 1  # Cooldown inicial
start_time = time.time()  # Marca quando o bot iniciou

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(name="🎮 OverPunch 🥊🔥"),
        status=discord.Status.online
    )
    print(f'✅ Bot conectado como {bot.user}')
    update_channel_name.start()

    # Sincroniza comandos de barra
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'✅ Comandos sincronizados: {len(synced)}')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

@tasks.loop(seconds=1)
async def update_channel_name():
    global cooldown_delay

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
                if response.status == 200:
                    data = await response.json()
                    jogando_agora = data['data'][0]['playing']

                    # Atualiza nome do canal
                    guild = bot.get_guild(GUILD_ID)
                    channel = guild.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.edit(name=f'〔🟢〕Active Counter: {jogando_agora}')
                    else:
                        print("❌ Canal não encontrado.")

                    # Atualiza status do bot (jogando)
                    await bot.change_presence(
                        activity=discord.Game(name=f"🎮 OverPunch 🥊🔥 | {jogando_agora} online"),
                        status=discord.Status.online
                    )

                    print(f'✅ Atualizado: {jogando_agora} jogadores')
                    cooldown_delay = 1
                else:
                    print(f'⚠️ API respondeu com erro: {response.status}')
                    cooldown_delay = min(cooldown_delay * 2, 300)

        except Exception as e:
            print(f'❌ Erro ao tentar atualizar: {e}')
            cooldown_delay = min(cooldown_delay * 2, 300)

    await asyncio.sleep(cooldown_delay)

# ================= ADMIN COMANDOS =====================
@tree.command(name="kick", description="Expulsa um usuário do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Usuário para expulsar", motivo="Motivo da expulsão")
async def kick_command(interaction: discord.Interaction, user: discord.Member, motivo: str = "Não especificado"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await user.kick(reason=motivo)
    await interaction.response.send_message(f"👢 {user.name} foi expulso. Motivo: {motivo}")

@tree.command(name="ban", description="Bane um usuário do servidor", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Usuário para banir", motivo="Motivo do banimento")
async def ban_command(interaction: discord.Interaction, user: discord.Member, motivo: str = "Não especificado"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    await user.ban(reason=motivo)
    await interaction.response.send_message(f"🔨 {user.name} foi banido. Motivo: {motivo}")

@tree.command(name="clear", description="Apaga mensagens de um canal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(quantidade="Quantidade de mensagens para apagar (máx 100)")
async def clear_command(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    if quantidade > 100:
        await interaction.response.send_message("⚠️ Você só pode apagar até 100 mensagens por vez.", ephemeral=True)
        return
    await interaction.channel.purge(limit=quantidade)
    await interaction.response.send_message(f"🧹 {quantidade} mensagens apagadas com sucesso.", ephemeral=True)

@tree.command(name="banlist", description="Lista de usuários banidos", guild=discord.Object(id=GUILD_ID))
async def banlist_command(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
        return
    bans = await interaction.guild.bans()
    if not bans:
        await interaction.response.send_message("✅ Nenhum usuário banido no servidor.", ephemeral=True)
    else:
        nomes = [f"{ban.user.name}#{ban.user.discriminator}" for ban in bans]
        await interaction.response.send_message("🔨 Banidos:\n" + "\n".join(nomes), ephemeral=True)

# ================== OUTROS COMANDOS =====================
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

@tree.command(name="status", description="Veja o status atual do bot e jogadores online", guild=discord.Object(id=GUILD_ID))
async def status_command(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                jogando_agora = data['data'][0]['playing']

                embed = discord.Embed(
                    title="📊 Status Atual",
                    description=f"Atualmente, **{jogando_agora}** pessoas estão jogando OverPunch 🥊🔥.",
                    color=0x00FF00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Não foi possível obter o status no momento.", ephemeral=True)

@tree.command(name="ping", description="Veja a latência do bot", guild=discord.Object(id=GUILD_ID))
async def ping_command(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latência: {latency}ms', ephemeral=True)

@tree.command(name="uptime", description="Veja há quanto tempo o bot está online", guild=discord.Object(id=GUILD_ID))
async def uptime_command(interaction: discord.Interaction):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    await interaction.response.send_message(f'🕒 Uptime: {uptime_str}', ephemeral=True)

@tree.command(name="jogo", description="Veja detalhes sobre o jogo OverPunch 🥊🔥", guild=discord.Object(id=GUILD_ID))
async def jogo_command(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}') as response:
            if response.status == 200:
                data = await response.json()
                jogo = data['data'][0]

                embed = discord.Embed(
                    title="📌 Informações do Jogo",
                    description=f"**OverPunch 🥊🔥**\n[🔗 Acessar no Roblox](https://www.roblox.com/games/137269319376582/OverPunch-NEW)",
                    color=0xFFD700
                )
                embed.set_thumbnail(url=jogo['thumbnails'][0]['imageUrl'] if jogo.get('thumbnails') else "https://tr.rbxcdn.com/3f688f75e6b2dc47c9738cd6dca3fcdf/150/150/Image/Png")
                embed.add_field(name="👑 Dono", value="kaua23193", inline=True)
                embed.add_field(name="👥 Jogando agora", value=str(jogo['playing']), inline=True)
                embed.set_footer(text="Powered by OverPunch")

                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                await interaction.response.send_message("❌ Não foi possível obter as informações do jogo.", ephemeral=True)

# Roda o bot
bot.run(TOKEN)
