import discord
from discord.ext import commands
import random
import string
import sqlite3
import datetime

# Discord Intent ayarları
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Veritabanı Kurulumu
conn = sqlite3.connect("keys.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS keys (
        key_code TEXT PRIMARY KEY,
        duration_days INTEGER,
        created_at TEXT,
        is_used INTEGER DEFAULT 0,
        used_by TEXT DEFAULT NULL
    )
''')
conn.commit()

def generate_key_string(prefix="AADIL"):
    # Format: AADIL-XXXX-XXXX-XXXX
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return f"{prefix}-" + "-".join(parts)

@bot.event
async def on_ready():
    print(f"Bot aktif: {bot.user.name} ({bot.user.id})")

@bot.command(name="genkey")
@commands.has_permissions(administrator=True)
async def gen_key(ctx, days: int = 1):
    """Yöneticiler için Key oluşturma komutu: !genkey <gün_sayısı>"""
    new_key = generate_key_string()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO keys (key_code, duration_days, created_at) VALUES (?, ?, ?)",
        (new_key, days, created_at)
    )
    conn.commit()

    embed = discord.Embed(title="🔑 Yeni Key Oluşturuldu", color=discord.Color.green())
    embed.add_field(name="Lisans Anahtarı", value=f"`{new_key}`", inline=False)
    embed.add_field(name="Süre", value=f"{days} Gün", inline=True)
    embed.set_footer(text="Aadil Mods Key System")

    await ctx.send(embed=embed)

@bot.command(name="redeem")
async def redeem_key(ctx, key_code: str):
    """Kullanıcıların key kullanması için komut: !redeem <key>"""
    cursor.execute("SELECT duration_days, is_used FROM keys WHERE key_code = ?", (key_code,))
    row = cursor.fetchone()

    if not row:
        await ctx.send("❌ Geçersiz veya hatalı bir key girdiniz.")
        return

    duration_days, is_used = row

    if is_used == 1:
        await ctx.send("⚠️ Bu key daha önce başka bir kullanıcı tarafından kullanılmış.")
        return

    # Key'i kullanıldı olarak işaretle
    cursor.execute(
        "UPDATE keys SET is_used = 1, used_by = ? WHERE key_code = ?",
        (str(ctx.author.id), key_code)
    )
    conn.commit()

    embed = discord.Embed(title="✅ Key Başarıyla Etkinleştirildi", color=discord.Color.blue())
    embed.add_field(name="Kullanıcı", value=ctx.author.mention, inline=True)
    embed.add_field(name="Erişim Süresi", value=f"{duration_days} Gün", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="check")
@commands.has_permissions(administrator=True)
async def check_key(ctx, key_code: str):
    """Yöneticiler için Key durum sorgulama: !check <key>"""
    cursor.execute("SELECT duration_days, created_at, is_used, used_by FROM keys WHERE key_code = ?", (key_code,))
    row = cursor.fetchone()

    if not row:
        await ctx.send("❌ Veritabanında böyle bir key bulunamadı.")
        return

    duration, created, is_used, used_by = row
    status = "Kullanıldı" if is_used else "Aktif / Kullanılmadı"
    user_str = f"<@{used_by}>" if used_by else "Yok"

    embed = discord.Embed(title="🔍 Key Bilgisi", color=discord.Color.orange())
    embed.add_field(name="Key", value=f"`{key_code}`", inline=False)
    embed.add_field(name="Süre", value=f"{duration} Gün", inline=True)
    embed.add_field(name="Durum", value=status, inline=True)
    embed.add_field(name="Kullanan", value=user_str, inline=False)

    await ctx.send(embed=embed)

# Bot Tokenini Buraya Girin
bot.run("DISCORD_BOT_TOKEN_BURAYA")
