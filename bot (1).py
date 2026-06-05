import discord
from discord.ext import commands
import random
import asyncio
import os
import aiohttp
import yt_dlp

# ─── AYARLAR ───────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")  # AI sohbet için (opsiyonel)
PREFIX = "!"
HOSGELDIN_KANAL = "genel"  # Hoşgeldin mesajı gönderilecek kanal adı
# ───────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ══════════════════════════════════════════════════════════
#  HAZIR OLUNCA
# ══════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ Bot açıldı: {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name=f"{PREFIX}yardım"))

# ══════════════════════════════════════════════════════════
#  HOŞGELDİN
# ══════════════════════════════════════════════════════════
@bot.event
async def on_member_join(member):
    kanal = discord.utils.get(member.guild.text_channels, name=HOSGELDIN_KANAL)
    if kanal:
        embed = discord.Embed(
            title=f"👋 Hoşgeldin, {member.name}!",
            description=f"**{member.guild.name}** sunucusuna hoş geldin!\nSunucumuzda iyi vakit geçirmen dileğiyle 🎉",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Sunucumuzda artık {member.guild.member_count} üye var!")
        await kanal.send(embed=embed)

# ══════════════════════════════════════════════════════════
#  YARDIM
# ══════════════════════════════════════════════════════════
@bot.command(name="yardım", aliases=["yardim", "help"])
async def yardim(ctx):
    embed = discord.Embed(title="📋 Komutlar", color=discord.Color.blurple())
    embed.add_field(name="🛡️ Moderasyon", value="`!ban` `!kick` `!mute` `!unmute` `!uyar` `!temizle`", inline=False)
    embed.add_field(name="🎵 Müzik", value="`!çal` `!dur` `!devam` `!atla` `!ses` `!çık`", inline=False)
    embed.add_field(name="🎮 Oyun", value="`!zar` `!yazıtura` `!tahmin` `!trivia` `!8top`", inline=False)
    embed.add_field(name="🤖 AI Sohbet", value="`!sor <soru>` — Claude AI ile konuş", inline=False)
    embed.add_field(name="ℹ️ Genel", value="`!ping` `!sunucu` `!kullanıcı`", inline=False)
    await ctx.send(embed=embed)

# ══════════════════════════════════════════════════════════
#  MODERASİYON
# ══════════════════════════════════════════════════════════
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, üye: discord.Member, *, sebep="Sebep belirtilmedi"):
    await üye.ban(reason=sebep)
    embed = discord.Embed(title="🔨 Ban", description=f"**{üye}** banlandı.\nSebep: {sebep}", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, üye: discord.Member, *, sebep="Sebep belirtilmedi"):
    await üye.kick(reason=sebep)
    embed = discord.Embed(title="👢 Kick", description=f"**{üye}** atıldı.\nSebep: {sebep}", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, üye: discord.Member, dakika: int = 10, *, sebep="Sebep belirtilmedi"):
    süre = discord.utils.utcnow() + asyncio.timedelta(minutes=dakika)
    await üye.timeout(süre, reason=sebep)
    embed = discord.Embed(title="🔇 Mute", description=f"**{üye}** {dakika} dakika susturuldu.\nSebep: {sebep}", color=discord.Color.yellow())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, üye: discord.Member):
    await üye.timeout(None)
    embed = discord.Embed(title="🔊 Unmute", description=f"**{üye}** susturması kaldırıldı.", color=discord.Color.green())
    await ctx.send(embed=embed)

uyarılar = {}

@bot.command()
@commands.has_permissions(kick_members=True)
async def uyar(ctx, üye: discord.Member, *, sebep="Sebep belirtilmedi"):
    uid = str(üye.id)
    uyarılar[uid] = uyarılar.get(uid, 0) + 1
    embed = discord.Embed(title="⚠️ Uyarı", description=f"**{üye}** uyarıldı! (Toplam: {uyarılar[uid]})\nSebep: {sebep}", color=discord.Color.gold())
    await ctx.send(embed=embed)
    if uyarılar[uid] >= 3:
        await üye.kick(reason="3 uyarı limitine ulaşıldı")
        await ctx.send(f"🚨 {üye} 3 uyarı aldığı için atıldı!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def temizle(ctx, adet: int = 10):
    await ctx.channel.purge(limit=adet + 1)
    msg = await ctx.send(f"🗑️ {adet} mesaj silindi.")
    await asyncio.sleep(3)
    await msg.delete()

# ══════════════════════════════════════════════════════════
#  MÜZİK
# ══════════════════════════════════════════════════════════
music_queue = {}
current_song = {}

YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

def get_audio_url(query):
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(query if query.startswith("http") else f"ytsearch:{query}", download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info.get('title', 'Bilinmeyen')

async def play_next(ctx):
    gid = ctx.guild.id
    if gid in music_queue and music_queue[gid]:
        query, title = music_queue[gid].pop(0)
        current_song[gid] = title
        url, title = await asyncio.get_event_loop().run_in_executor(None, get_audio_url, query)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTS)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(embed=discord.Embed(title="🎵 Çalıyor", description=title, color=discord.Color.purple()))

@bot.command(name="çal", aliases=["cal", "play"])
async def cal(ctx, *, sorgu):
    if not ctx.author.voice:
        return await ctx.send("❌ Önce bir ses kanalına gir!")
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    gid = ctx.guild.id
    if gid not in music_queue:
        music_queue[gid] = []

    if ctx.voice_client.is_playing():
        music_queue[gid].append((sorgu, sorgu))
        await ctx.send(f"➕ Sıraya eklendi: **{sorgu}**")
    else:
        music_queue[gid].insert(0, (sorgu, sorgu))
        await play_next(ctx)

@bot.command(name="dur", aliases=["pause"])
async def dur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Duraklatıldı.")

@bot.command(name="devam", aliases=["resume"])
async def devam(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Devam ediyor.")

@bot.command(name="atla", aliases=["skip"])
async def atla(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Atlandı.")

@bot.command(name="ses", aliases=["volume", "vol"])
async def ses(ctx, seviye: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)
        ctx.voice_client.source.volume = seviye / 100
        await ctx.send(f"🔊 Ses: {seviye}%")

@bot.command(name="çık", aliases=["cik", "leave", "dc"])
async def cik(ctx):
    if ctx.voice_client:
        music_queue[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Ses kanalından çıkıldı.")

# ══════════════════════════════════════════════════════════
#  OYUNLAR
# ══════════════════════════════════════════════════════════
@bot.command()
async def zar(ctx, adet: int = 1, yüz: int = 6):
    sonuçlar = [random.randint(1, yüz) for _ in range(min(adet, 10))]
    await ctx.send(f"🎲 **{', '.join(map(str, sonuçlar))}** (Toplam: {sum(sonuçlar)})")

@bot.command(name="yazıtura", aliases=["yazitura", "flip"])
async def yazıtura(ctx):
    sonuç = random.choice(["🪙 Yazı", "🪙 Tura"])
    await ctx.send(sonuç)

tahmin_oyunları = {}

@bot.command()
async def tahmin(ctx):
    if ctx.channel.id in tahmin_oyunları:
        return await ctx.send("⚠️ Bu kanalda zaten aktif bir oyun var!")
    sayi = random.randint(1, 100)
    tahmin_oyunları[ctx.channel.id] = sayi
    await ctx.send("🔢 1-100 arasında bir sayı tuttum! `!say <sayı>` ile tahmin et.")

@bot.command()
async def say(ctx, sayı: int):
    if ctx.channel.id not in tahmin_oyunları:
        return await ctx.send("❌ Aktif bir oyun yok. `!tahmin` ile başlat.")
    gizli = tahmin_oyunları[ctx.channel.id]
    if sayı < gizli:
        await ctx.send("📈 Daha büyük!")
    elif sayı > gizli:
        await ctx.send("📉 Daha küçük!")
    else:
        del tahmin_oyunları[ctx.channel.id]
        await ctx.send(f"🎉 **{ctx.author.mention} bildi! Sayı {gizli} idi!**")

trivia_sorular = [
    ("Türkiye'nin başkenti neresidir?", "Ankara"),
    ("Dünyanın en büyük okyanusu hangisidir?", "Pasifik"),
    ("Python hangi yılda oluşturuldu?", "1991"),
    ("Discord hangi yılda kuruldu?", "2015"),
    ("Güneş sistemimizdeki en büyük gezegen hangisidir?", "Jüpiter"),
    ("Su'nun kimyasal formülü nedir?", "H2O"),
    ("Türkiye kaç ilden oluşur?", "81"),
]

@bot.command()
async def trivia(ctx):
    soru, cevap = random.choice(trivia_sorular)
    embed = discord.Embed(title="🧠 Trivia", description=soru, color=discord.Color.teal())
    embed.set_footer(text="30 saniye içinde cevapla!")
    await ctx.send(embed=embed)

    def kontrol(m):
        return m.channel == ctx.channel and not m.author.bot

    try:
        mesaj = await bot.wait_for("message", timeout=30.0, check=kontrol)
        if mesaj.content.lower() == cevap.lower():
            await ctx.send(f"✅ **{mesaj.author.mention} doğru bildi!** Cevap: **{cevap}**")
        else:
            await ctx.send(f"❌ Yanlış! Doğru cevap: **{cevap}**")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Süre doldu! Cevap: **{cevap}**")

@bot.command(name="8top", aliases=["8ball"])
async def sekiz_top(ctx, *, soru):
    cevaplar = [
        "✅ Kesinlikle evet!", "✅ Evet.", "✅ Büyük ihtimalle.",
        "🤔 Emin değilim.", "🤔 Belirsiz.",
        "❌ Sanmıyorum.", "❌ Hayır.", "❌ Kesinlikle hayır!"
    ]
    await ctx.send(f"🎱 **{random.choice(cevaplar)}**")

# ══════════════════════════════════════════════════════════
#  AI SOHBET (Anthropic Claude)
# ══════════════════════════════════════════════════════════
@bot.command(name="sor")
async def sor(ctx, *, soru):
    if not ANTHROPIC_API_KEY:
        return await ctx.send("❌ AI özelliği için `ANTHROPIC_API_KEY` gerekli!")

    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 500,
                        "system": "Sen yardımcı bir Discord botusun. Türkçe ve kısa cevap ver.",
                        "messages": [{"role": "user", "content": soru}]
                    }
                ) as resp:
                    data = await resp.json()
                    cevap = data["content"][0]["text"]
                    embed = discord.Embed(
                        title="🤖 AI Cevabı",
                        description=cevap[:4000],
                        color=discord.Color.blurple()
                    )
                    embed.set_footer(text=f"Soran: {ctx.author}")
                    await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Hata: {e}")

# ══════════════════════════════════════════════════════════
#  BİLGİ KOMUTLARI
# ══════════════════════════════════════════════════════════
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! **{round(bot.latency * 1000)}ms**")

@bot.command(name="sunucu", aliases=["server"])
async def sunucu(ctx):
    g = ctx.guild
    embed = discord.Embed(title=g.name, color=discord.Color.blurple())
    embed.add_field(name="👥 Üyeler", value=g.member_count)
    embed.add_field(name="📅 Kuruldu", value=g.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="👑 Sahip", value=g.owner)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="kullanıcı", aliases=["kullanici", "user", "kim"])
async def kullanici(ctx, üye: discord.Member = None):
    üye = üye or ctx.author
    embed = discord.Embed(title=str(üye), color=discord.Color.blurple())
    embed.add_field(name="🆔 ID", value=üye.id)
    embed.add_field(name="📅 Katıldı", value=üye.joined_at.strftime("%d/%m/%Y"))
    embed.set_thumbnail(url=üye.display_avatar.url)
    await ctx.send(embed=embed)

# ══════════════════════════════════════════════════════════
#  HATA YÖNETİMİ
# ══════════════════════════════════════════════════════════
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanmak için yetkin yok!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Kullanıcı bulunamadı!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Eksik parametre! `{PREFIX}yardım` ile komutlara bak.")
    elif isinstance(error, commands.CommandNotFound):
        pass

# ══════════════════════════════════════════════════════════
bot.run(TOKEN)
