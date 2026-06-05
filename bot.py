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
    embed.add_field(name="🎉 Çekiliş", value="`!çekiliş <dakika> <kazanan> <tr/en> <ödül>`", inline=False)
    embed.add_field(name="📊 Anket", value='`!anket "Soru?" "A" "B"` | `!anketkapat <mesaj_id>`', inline=False)
    embed.add_field(name="🎰 Slot", value="`!slot` — Slot çevir | `!slotdaily` — Bonus | `!slotbakiye`", inline=False)
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
#  ÇEKİLİŞ SİSTEMİ
# ══════════════════════════════════════════════════════════
cekilisler = {}  # message_id -> {katılımcılar, ödül, bitiş, dil, kanal}

LANG = {
    "tr": {
        "title": "🎉 ÇEKİLİŞ",
        "prize": "Ödül",
        "duration": "Süre",
        "winner_count": "Kazanan Sayısı",
        "join_btn": "🎟️ Katıl",
        "participants": "Katılımcı",
        "ended": "🏆 Çekiliş Bitti!",
        "winners": "Kazananlar",
        "no_winner": "Geçerli katılımcı yok.",
        "joined": "✅ Çekilişe katıldın!",
        "already": "⚠️ Zaten katılmışsın!",
        "footer": "Katılmak için butona tıkla!",
        "min_unit": "dakika",
    },
    "en": {
        "title": "🎉 GIVEAWAY",
        "prize": "Prize",
        "duration": "Duration",
        "winner_count": "Winners",
        "join_btn": "🎟️ Join",
        "participants": "Participants",
        "ended": "🏆 Giveaway Ended!",
        "winners": "Winners",
        "no_winner": "No valid participants.",
        "joined": "✅ You joined the giveaway!",
        "already": "⚠️ You already joined!",
        "footer": "Click the button to join!",
        "min_unit": "minutes",
    }
}

class CekilisButon(discord.ui.View):
    def __init__(self, msg_id, dil="tr"):
        super().__init__(timeout=None)
        self.msg_id = msg_id
        self.dil = dil
        self.join_button.label = LANG[dil]["join_btn"]

    @discord.ui.button(label="🎟️ Katıl", style=discord.ButtonStyle.green, custom_id="cekiliskatil")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        l = LANG[self.dil]
        if self.msg_id not in cekilisler:
            return await interaction.response.send_message("❌", ephemeral=True)
        veri = cekilisler[self.msg_id]
        uid = interaction.user.id
        if uid in veri["katılımcılar"]:
            return await interaction.response.send_message(l["already"], ephemeral=True)
        veri["katılımcılar"].add(uid)
        await interaction.response.send_message(l["joined"], ephemeral=True)
        # Embed güncelle
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name=f"👥 {l['participants']}", value=str(len(veri["katılımcılar"])), inline=True)
        await interaction.message.edit(embed=embed)

@bot.command(name="çekiliş", aliases=["cekilisbaslat", "giveaway"])
@commands.has_permissions(manage_guild=True)
async def cekilisbaslat(ctx, süre: int, kazanan: int, dil: str = "tr", *, ödül: str):
    """!çekiliş <süre_dakika> <kazanan_sayısı> <dil:tr/en> <ödül>"""
    if dil not in LANG:
        dil = "tr"
    l = LANG[dil]
    bitis = discord.utils.utcnow().timestamp() + süre * 60

    embed = discord.Embed(title=l["title"], color=discord.Color.gold())
    embed.add_field(name=f"🎁 {l['prize']}", value=ödül, inline=False)
    embed.add_field(name=f"⏱️ {l['duration']}", value=f"{süre} {l['min_unit']}", inline=True)
    embed.add_field(name=f"🏆 {l['winner_count']}", value=str(kazanan), inline=True)
    embed.add_field(name=f"👥 {l['participants']}", value="0", inline=True)
    embed.set_footer(text=l["footer"])
    embed.timestamp = discord.utils.utcnow()

    view = CekilisButon(None, dil)
    msg = await ctx.send(embed=embed, view=view)
    view.msg_id = msg.id

    cekilisler[msg.id] = {
        "katılımcılar": set(),
        "kazanan": kazanan,
        "bitis": bitis,
        "dil": dil,
        "kanal": ctx.channel,
        "ödül": ödül,
        "mesaj": msg,
    }

    await asyncio.sleep(süre * 60)

    # Çekilişi bitir
    veri = cekilisler.pop(msg.id, None)
    if not veri:
        return
    l = LANG[veri["dil"]]
    katılımcılar = list(veri["katılımcılar"])
    if not katılımcılar:
        kazananlar_str = l["no_winner"]
    else:
        seçilenler = random.sample(katılımcılar, min(veri["kazanan"], len(katılımcılar)))
        kazananlar_str = " ".join(f"<@{u}>" for u in seçilenler)

    embed2 = discord.Embed(title=l["ended"], color=discord.Color.red())
    embed2.add_field(name=f"🎁 {l['prize']}", value=veri["ödül"], inline=False)
    embed2.add_field(name=f"🏆 {l['winners']}", value=kazananlar_str, inline=False)
    embed2.timestamp = discord.utils.utcnow()
    await veri["mesaj"].edit(embed=embed2, view=None)
    await veri["kanal"].send(f"🎉 {l['ended']} | {l['prize']}: **{veri['ödül']}** | {l['winners']}: {kazananlar_str}")

# ══════════════════════════════════════════════════════════
#  ANKET SİSTEMİ
# ══════════════════════════════════════════════════════════
anketler = {}  # message_id -> {soru, seçenekler, oylar, oy_verenler}

class AnketButon(discord.ui.View):
    def __init__(self, msg_id, seçenekler):
        super().__init__(timeout=None)
        for i, seçenek in enumerate(seçenekler[:5]):
            harfler = ["🅰️", "🅱️", "🇨", "🇩", "🇪"]
            btn = discord.ui.Button(
                label=seçenek[:60],
                style=discord.ButtonStyle.primary,
                emoji=harfler[i],
                custom_id=f"anket_{msg_id}_{i}"
            )
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, idx):
        async def callback(interaction: discord.Interaction):
            msg_id = interaction.message.id
            if msg_id not in anketler:
                return await interaction.response.send_message("❌ Anket bulunamadı.", ephemeral=True)
            veri = anketler[msg_id]
            uid = interaction.user.id
            if uid in veri["oy_verenler"]:
                eski = veri["oy_verenler"][uid]
                veri["oylar"][eski] -= 1
            veri["oy_verenler"][uid] = idx
            veri["oylar"][idx] += 1
            # Embed güncelle
            toplam = sum(veri["oylar"])
            embed = interaction.message.embeds[0]
            embed.clear_fields()
            for i, seç in enumerate(veri["seçenekler"]):
                oy = veri["oylar"][i]
                yüzde = (oy / toplam * 100) if toplam > 0 else 0
                bar = "█" * int(yüzde / 10) + "░" * (10 - int(yüzde / 10))
                embed.add_field(
                    name=f"{'🅰️🅱️🇨🇩🇪'[i*2:i*2+2] if i < 2 else ['🇨','🇩','🇪'][i-2]} {seç}",
                    value=f"`{bar}` {oy} oy ({yüzde:.1f}%)",
                    inline=False
                )
            embed.set_footer(text=f"Toplam oy: {toplam} | Oy değiştirilebilir")
            await interaction.message.edit(embed=embed)
            await interaction.response.send_message(f"✅ Oyun **{veri['seçenekler'][idx]}** için kaydedildi!", ephemeral=True)
        return callback

@bot.command(name="anket")
async def anket(ctx, soru: str, *seçenekler):
    """!anket "Soru?" "Seçenek 1" "Seçenek 2" ..."""
    if len(seçenekler) < 2:
        return await ctx.send("❌ En az 2 seçenek gir!\nKullanım: `!anket \"Soru?\" \"Seçenek 1\" \"Seçenek 2\"`")
    if len(seçenekler) > 5:
        return await ctx.send("❌ En fazla 5 seçenek girebilirsin!")

    embed = discord.Embed(title=f"📊 {soru}", color=discord.Color.blue())
    oylar = [0] * len(seçenekler)
    harfler = ["🅰️", "🅱️", "🇨", "🇩", "🇪"]
    for i, seç in enumerate(seçenekler):
        embed.add_field(
            name=f"{harfler[i]} {seç}",
            value="`░░░░░░░░░░` 0 oy (0.0%)",
            inline=False
        )
    embed.set_footer(text="Toplam oy: 0 | Oy değiştirilebilir")
    embed.set_author(name=f"Anket: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

    msg = await ctx.send(embed=embed)

    anketler[msg.id] = {
        "soru": soru,
        "seçenekler": list(seçenekler),
        "oylar": oylar,
        "oy_verenler": {},
    }

    view = AnketButon(msg.id, list(seçenekler))
    await msg.edit(view=view)

@bot.command(name="anketbitter", aliases=["anketkapat"])
@commands.has_permissions(manage_guild=True)
async def anketkapat(ctx, mesaj_id: int):
    """Anketi kapatır ve sonuçları gösterir."""
    if mesaj_id not in anketler:
        return await ctx.send("❌ Bu ID'ye ait aktif anket bulunamadı.")
    veri = anketler.pop(mesaj_id)
    toplam = sum(veri["oylar"])
    embed = discord.Embed(title=f"📊 [KAPANDI] {veri['soru']}", color=discord.Color.red())
    kazanan_idx = veri["oylar"].index(max(veri["oylar"])) if toplam > 0 else None
    for i, seç in enumerate(veri["seçenekler"]):
        oy = veri["oylar"][i]
        yüzde = (oy / toplam * 100) if toplam > 0 else 0
        bar = "█" * int(yüzde / 10) + "░" * (10 - int(yüzde / 10))
        suffix = " 🏆" if i == kazanan_idx and toplam > 0 else ""
        embed.add_field(
            name=f"{seç}{suffix}",
            value=f"`{bar}` {oy} oy ({yüzde:.1f}%)",
            inline=False
        )
    embed.set_footer(text=f"Toplam oy: {toplam} | Anket kapatıldı.")
    await ctx.send(embed=embed)

# ══════════════════════════════════════════════════════════
#  SLOT MAKİNESİ
# ══════════════════════════════════════════════════════════
SLOT_SEMBOLLER = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
SLOT_ÖDÜLLER = {
    ("💎", "💎", "💎"): ("JACKPOT! 💎", 100),
    ("7️⃣", "7️⃣", "7️⃣"): ("MEGA WIN! 7️⃣", 50),
    ("⭐", "⭐", "⭐"): ("BIG WIN! ⭐", 25),
    ("🍇", "🍇", "🍇"): ("WIN! 🍇", 15),
    ("🍊", "🍊", "🍊"): ("WIN! 🍊", 10),
    ("🍋", "🍋", "🍋"): ("WIN! 🍋", 8),
    ("🍒", "🍒", "🍒"): ("WIN! 🍒", 5),
}

slot_bakiye = {}  # user_id -> bakiye (başlangıç 100)
slot_son_oyun = {}  # user_id -> timestamp (cooldown)

SLOT_BAŞLANGIÇ = 100
SLOT_BAHIS = 10
SLOT_COOLDOWN = 10  # saniye

async def slot_animasyon(msg, s1, s2, s3):
    """Slot dönerken animasyon göster"""
    karışık = SLOT_SEMBOLLER
    for _ in range(3):
        a, b, c = random.choices(karışık, k=3)
        embed = discord.Embed(title="🎰 Slot Makinesi", color=discord.Color.yellow())
        embed.add_field(name="‎", value=f"┌─────────────┐\n│ {a}  ❓  ❓ │\n└─────────────┘", inline=False)
        embed.set_footer(text="Dönüyor...")
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)
    for _ in range(3):
        b_r, c_r = random.choices(karışık, k=2)
        embed = discord.Embed(title="🎰 Slot Makinesi", color=discord.Color.yellow())
        embed.add_field(name="‎", value=f"┌─────────────┐\n│ {s1}  {b_r}  ❓ │\n└─────────────┘", inline=False)
        embed.set_footer(text="Dönüyor...")
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)
    for _ in range(3):
        embed = discord.Embed(title="🎰 Slot Makinesi", color=discord.Color.yellow())
        embed.add_field(name="‎", value=f"┌─────────────┐\n│ {s1}  {s2}  ❓ │\n└─────────────┘", inline=False)
        embed.set_footer(text="Dönüyor...")
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)

@bot.command(name="slot")
async def slot(ctx):
    """!slot — Slot makinesini çevir (her 10 saniyede bir)"""
    uid = ctx.author.id
    şimdi = asyncio.get_event_loop().time()

    # Cooldown kontrolü
    if uid in slot_son_oyun:
        kalan = SLOT_COOLDOWN - (şimdi - slot_son_oyun[uid])
        if kalan > 0:
            return await ctx.send(f"⏳ {kalan:.1f} saniye bekle!")

    # Bakiye kontrolü
    if uid not in slot_bakiye:
        slot_bakiye[uid] = SLOT_BAŞLANGIÇ
    bakiye = slot_bakiye[uid]

    if bakiye < SLOT_BAHIS:
        return await ctx.send(f"❌ Yetersiz bakiye! ({bakiye} 🪙) `!slotdaily` ile bonus al.")

    slot_son_oyun[uid] = şimdi
    slot_bakiye[uid] -= SLOT_BAHIS

    # Slot çek
    ağırlıklar = [30, 25, 20, 12, 8, 3, 2]
    s1, s2, s3 = random.choices(SLOT_SEMBOLLER, weights=ağırlıklar, k=3)

    # Animasyon
    embed_start = discord.Embed(title="🎰 Slot Makinesi", color=discord.Color.yellow())
    embed_start.add_field(name="‎", value="┌─────────────┐\n│ ❓  ❓  ❓ │\n└─────────────┘", inline=False)
    embed_start.set_footer(text="Dönüyo
