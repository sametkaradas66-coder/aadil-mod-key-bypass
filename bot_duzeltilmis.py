import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai
import json
import os
import random
import asyncio

load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

SETTINGS_FILE = "kanallar.json"

def load_data():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

kanallar = load_data()

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kanal(ctx, channel: discord.TextChannel):
    kanallar[str(ctx.guild.id)] = channel.id
    save_data(kanallar)
    await ctx.send(f"✅ AI sohbet kanalı ayarlandı: {channel.mention}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def yazitura(ctx):
    await ctx.send(f"🪙 {random.choice(['Yazı','Tura'])}")

@bot.command()
async def zar(ctx):
    await ctx.send(f"🎲 {random.randint(1,6)}")

@bot.command()
async def yardim(ctx):
    await ctx.send("""
📜 Komutlar

!ping
!zar
!yazitura
!avatar
!sunucu
!ban @uye sebep
!kick @uye sebep
!sil miktar
!cekilis dakika ödül
!kanal #kanal
""")

@bot.command()
async def avatar(ctx, uye: discord.Member = None):
    uye = uye or ctx.author
    embed = discord.Embed(title=f"{uye.name} Avatarı")
    embed.set_image(url=uye.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def sunucu(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=guild.name)
    embed.add_field(name="Üye Sayısı", value=guild.member_count)
    embed.add_field(name="Sunucu ID", value=guild.id)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, uye: discord.Member, *, sebep="Sebep belirtilmedi"):
    await uye.kick(reason=sebep)
    await ctx.send(f"👢 {uye} atıldı.\nSebep: {sebep}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, uye: discord.Member, *, sebep="Sebep belirtilmedi"):
    await uye.ban(reason=sebep)
    await ctx.send(f"🔨 {uye} banlandı.\nSebep: {sebep}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
    await ctx.channel.purge(limit=miktar + 1)
    msg = await ctx.send(f"🗑️ {miktar} mesaj silindi.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def cekilis(ctx, dakika: int, *, odul):
    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ",
        description=f"Ödül: **{odul}**\n\nKatılmak için 🎉 emojisine bas."
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

    await asyncio.sleep(dakika * 60)

    msg = await ctx.channel.fetch_message(msg.id)
    reaction = discord.utils.get(msg.reactions, emoji="🎉")

    users = []
    async for user in reaction.users():
        if not user.bot:
            users.append(user)

    if not users:
        await ctx.send("❌ Katılan olmadı.")
        return

    kazanan = random.choice(users)
    await ctx.send(f"🏆 Kazanan: {kazanan.mention}\nÖdül: **{odul}**")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild:
        guild_id = str(message.guild.id)

        if guild_id in kanallar and message.channel.id == kanallar[guild_id]:
            thinking = await message.reply("🧠 düşünüyorum...")

            try:
                response = model.generate_content(
                    f"Kullanıcı: {message.content}\nKısa ve Türkçe cevap ver."
                )

                cevap = response.text
                await thinking.delete()

                if len(cevap) > 2000:
                    for i in range(0, len(cevap), 1900):
                        await message.channel.send(cevap[i:i+1900])
                else:
                    await message.channel.send(cevap)

            except Exception as e:
                await thinking.edit(content=f"❌ Hata: {e}")

    await bot.process_commands(message)

bot.run(TOKEN)
