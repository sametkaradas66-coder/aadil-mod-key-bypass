
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os, random

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class TuffGuyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = TuffGuyBot()

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")

# GENEL

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency*1000)}ms")

@bot.tree.command(name="yardim")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 TuffGuy Bot", color=0x5865F2)
    embed.add_field(name="🎮 Eğlence", value="/zar /yazitura /8ball /ship", inline=False)
    embed.add_field(name="🛠️ Genel", value="/ping /userinfo /botinfo", inline=False)
    embed.add_field(name="🔨 Moderasyon", value="/ban /kick /sil /duyuru /kilit /ac /slowmode /warn /unban", inline=False)
    embed.add_field(name="🎉 Sistem", value="/cekilis", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, uye: discord.Member=None):
    uye = uye or interaction.user
    embed = discord.Embed(title=f"👤 {uye}")
    embed.add_field(name="ID", value=str(uye.id))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="botinfo")
async def botinfo(interaction: discord.Interaction):
    await interaction.response.send_message(f"🤖 {len(bot.guilds)} sunucu")

# EĞLENCE

@bot.tree.command(name="zar")
async def zar(interaction: discord.Interaction):
    await interaction.response.send_message(f"🎲 {random.randint(1,6)}")

@bot.tree.command(name="yazitura")
async def yazitura(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["🪙 Yazı","🪙 Tura"]))

@bot.tree.command(name="ship")
async def ship(interaction: discord.Interaction, uye1:discord.Member, uye2:discord.Member):
    await interaction.response.send_message(f"❤️ Uyum: %{random.randint(1,100)}")

@bot.tree.command(name="8ball")
async def eightball(interaction: discord.Interaction, soru:str):
    await interaction.response.send_message(random.choice(["Evet","Hayır","Belki","Kesinlikle","Sanmam"]))

# ÇEKİLİŞ

@bot.tree.command(name="cekilis")
async def cekilis(interaction: discord.Interaction, sure:int, kazanan:int, odul:str, cekilis_sahibi:str):
    embed = discord.Embed(title="🎉 GIVEAWAY", color=0xFEE75C)
    embed.add_field(name="⏰ Süre", value=f"{sure} dk")
    embed.add_field(name="🥇 Kazanan", value=str(kazanan))
    embed.add_field(name="🏆 Ödül", value=odul, inline=False)
    embed.set_footer(text=f"👑 {cekilis_sahibi}")
    await interaction.response.send_message(embed=embed)

# MODERASYON

@bot.tree.command(name="ban")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep:str="Belirtilmedi"):
    await uye.ban(reason=sebep)
    await interaction.response.send_message(f"🔨 {uye} banlandı.")

@bot.tree.command(name="kick")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, uye: discord.Member, sebep:str="Belirtilmedi"):
    await uye.kick(reason=sebep)
    await interaction.response.send_message(f"👢 {uye} atıldı.")

@bot.tree.command(name="sil")
@app_commands.default_permissions(manage_messages=True)
async def sil(interaction: discord.Interaction, miktar:int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🗑️ {miktar} mesaj silindi.", ephemeral=True)

@bot.tree.command(name="duyuru")
@app_commands.default_permissions(administrator=True)
async def duyuru(interaction: discord.Interaction, mesaj:str):
    await interaction.response.send_message(f"📢 {mesaj}")

@bot.tree.command(name="kilit")
@app_commands.default_permissions(manage_channels=True)
async def kilit(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Kanal kilitlendi")

@bot.tree.command(name="ac")
@app_commands.default_permissions(manage_channels=True)
async def ac(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Kanal açıldı")

@bot.tree.command(name="slowmode")
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, saniye:int):
    await interaction.channel.edit(slowmode_delay=saniye)
    await interaction.response.send_message(f"🐢 Slowmode {saniye}s")

@bot.tree.command(name="warn")
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, uye:discord.Member, sebep:str):
    await interaction.response.send_message(f"⚠️ {uye.mention} uyarıldı. Sebep: {sebep}")

@bot.tree.command(name="unban")
@app_commands.default_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, kullanici_id:str):
    await interaction.response.send_message(f"✅ Unban sistemi için ID: {kullanici_id}")

bot.run(TOKEN)
