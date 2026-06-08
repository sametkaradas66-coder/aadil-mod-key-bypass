import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os, random, asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class TuffGuyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = TuffGuyBot(command_prefix="!", intents=intents)

# ---------- MODERN USERINFO ----------

@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, uye: discord.Member = None):
    uye = uye or interaction.user

    embed = discord.Embed(
        title=f"👤 {uye.display_name}",
        description="Kullanıcı Bilgileri",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.add_field(name="🆔 ID", value=f"`{uye.id}`", inline=False)
    embed.add_field(name="🎖️ En Yüksek Rol", value=uye.top_role.mention, inline=False)

    if uye.joined_at:
        embed.add_field(
            name="📥 Katılım",
            value=f"<t:{int(uye.joined_at.timestamp())}:F>",
            inline=False
        )

    embed.add_field(
        name="📅 Hesap Oluşturma",
        value=f"<t:{int(uye.created_at.timestamp())}:F>",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ---------- MODERN BOTINFO ----------

@bot.tree.command(name="botinfo")
async def botinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 TuffGuy Bot",
        description="Bot İstatistikleri",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="🌍 Sunucu", value=len(bot.guilds))
    embed.add_field(name="👥 Kullanıcı", value=len(bot.users))
    embed.add_field(name="🏓 Ping", value=f"{round(bot.latency*1000)}ms")
    await interaction.response.send_message(embed=embed)

# ---------- GIVEAWAY ----------

class GiveawayView(discord.ui.View):
    def __init__(self, kazanan_sayisi, odul):
        super().__init__(timeout=None)
        self.katilanlar = set()
        self.kazanan_sayisi = kazanan_sayisi
        self.odul = odul

    @discord.ui.button(label="Katıl", emoji="🎉", style=discord.ButtonStyle.green)
    async def katil(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.katilanlar:
            await interaction.response.send_message(
                "❌ Zaten katıldın.",
                ephemeral=True
            )
            return

        self.katilanlar.add(interaction.user.id)

        await interaction.response.send_message(
            "✅ Çekilişe katıldın!",
            ephemeral=True
        )

@bot.tree.command(name="cekilis")
async def cekilis(
    interaction: discord.Interaction,
    sure: str,
    kazanan: int,
    odul: str,
    cekilis_sahibi: str
):

    sureler = {
        "1 Saat": 3600,
        "2 Saat": 7200,
        "6 Saat": 21600,
        "12 Saat": 43200,
        "1 Gün": 86400,
        "3 Gün": 259200,
        "7 Gün": 604800
    }

    saniye = sureler.get(sure, 3600)

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description="Butona basarak katıl!",
        color=0xFEE75C
    )

    embed.add_field(name="🏆 Ödül", value=odul, inline=False)
    embed.add_field(name="⏰ Süre", value=sure)
    embed.add_field(name="🥇 Kazanan", value=str(kazanan))
    embed.set_footer(text=f"👑 {cekilis_sahibi}")

    view = GiveawayView(kazanan, odul)

    await interaction.response.send_message(embed=embed, view=view)

    mesaj = await interaction.original_response()

    await asyncio.sleep(saniye)

    if not view.katilanlar:
        await mesaj.reply("❌ Katılımcı yok.")
        return

    kazananlar = random.sample(
        list(view.katilanlar),
        min(kazanan, len(view.katilanlar))
    )

    mentions = [f"<@{x}>" for x in kazananlar]

    await mesaj.reply(
        f"🏆 Kazanan(lar): {', '.join(mentions)}\n🎁 Ödül: {odul}"
    )



# ===== EXTRA MODERN COMMANDS =====

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(title="🏓 Pong!", description=f"{round(bot.latency*1000)}ms", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="zar")
async def zar(interaction: discord.Interaction):
    import random
    embed = discord.Embed(title="🎲 Zar", description=f"Sonuç: **{random.randint(1,6)}**", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="yazitura")
async def yazitura(interaction: discord.Interaction):
    import random
    await interaction.response.send_message(embed=discord.Embed(
        title="🪙 Yazı Tura",
        description=random.choice(["Yazı","Tura"]),
        color=discord.Color.blurple()
    ))

@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, uye: discord.Member=None):
    uye = uye or interaction.user
    embed = discord.Embed(title=f"🖼️ {uye.display_name}")
    embed.set_image(url=uye.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kick")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, uye: discord.Member, sebep:str="Belirtilmedi"):
    await uye.kick(reason=sebep)
    await interaction.response.send_message(embed=discord.Embed(title="👢 Kick",description=f"{uye.mention} atıldı."))

@bot.tree.command(name="ban")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep:str="Belirtilmedi"):
    await uye.ban(reason=sebep)
    await interaction.response.send_message(embed=discord.Embed(title="🔨 Ban",description=f"{uye.mention} yasaklandı."))

@bot.tree.command(name="sil")
@app_commands.default_permissions(manage_messages=True)
async def sil(interaction: discord.Interaction, miktar:int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🗑️ {miktar} mesaj silindi.", ephemeral=True)





# ===== ULTRA V3 EK PAKET =====

@bot.tree.command(name="warn")
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, uye: discord.Member, sebep: str):
    e = discord.Embed(title="⚠️ Uyarı", description=f"{uye.mention}\nSebep: {sebep}", color=discord.Color.orange())
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="slowmode")
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, saniye: int):
    await interaction.channel.edit(slowmode_delay=saniye)
    await interaction.response.send_message(embed=discord.Embed(
        title="🐢 Slowmode",
        description=f"{saniye} saniye olarak ayarlandı.",
        color=discord.Color.blurple()
    ))

@bot.tree.command(name="kilit")
@app_commands.default_permissions(manage_channels=True)
async def kilit(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Kanal kilitlendi.")

@bot.tree.command(name="ac")
@app_commands.default_permissions(manage_channels=True)
async def ac(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Kanal açıldı.")

@bot.tree.command(name="ship")
async def ship(interaction: discord.Interaction, uye1: discord.Member, uye2: discord.Member):
    import random
    oran = random.randint(1,100)
    await interaction.response.send_message(embed=discord.Embed(
        title="❤️ Ship",
        description=f"{uye1.mention} × {uye2.mention}\nUyum: %{oran}",
        color=discord.Color.red()
    ))

@bot.tree.command(name="8ball")
async def eightball(interaction: discord.Interaction, soru: str):
    import random
    cevaplar = ["Evet","Hayır","Belki","Kesinlikle","Sanmam"]
    await interaction.response.send_message(embed=discord.Embed(
        title="🎱 8Ball",
        description=random.choice(cevaplar),
        color=discord.Color.dark_purple()
    ))





# ===== ULTRA V5 SISTEMLER =====

# Basit ticket paneli
class TicketView(discord.ui.View):
    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.blurple)
    async def ticket_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        kanal = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )
        await interaction.response.send_message(
            f"✅ Ticket oluşturuldu: {kanal.mention}",
            ephemeral=True
        )

@bot.tree.command(name="ticketpanel")
@app_commands.default_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Destek Sistemi",
        description="Butona basarak ticket açabilirsiniz.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

# Basit yardım menüsü
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Genel"),
            discord.SelectOption(label="Moderasyon"),
            discord.SelectOption(label="Eğlence"),
        ]
        super().__init__(placeholder="Kategori seç...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"📂 Seçilen kategori: {self.values[0]}",
            ephemeral=True
        )

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

@bot.tree.command(name="yardimv2")
async def yardimv2(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Yardım Menüsü",
        description="Aşağıdan kategori seç.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=HelpView())

# Otorol (hafif sürüm)
OTOROL_ID = None

@bot.event
async def on_member_join(member):
    if OTOROL_ID:
        rol = member.guild.get_role(OTOROL_ID)
        if rol:
            await member.add_roles(rol)





# ===== ULTRA V6 EKSTRALAR =====

LOG_CHANNEL_ID = None  # log kanal ID

@bot.event
async def on_member_remove(member):
    if LOG_CHANNEL_ID:
        kanal = bot.get_channel(LOG_CHANNEL_ID)
        if kanal:
            e = discord.Embed(
                title="👋 Üye Ayrıldı",
                description=f"{member} sunucudan ayrıldı.",
                color=discord.Color.red()
            )
            await kanal.send(embed=e)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if LOG_CHANNEL_ID:
        kanal = bot.get_channel(LOG_CHANNEL_ID)
        if kanal:
            e = discord.Embed(
                title="🗑️ Mesaj Silindi",
                description=message.content[:1000] or "İçerik yok",
                color=discord.Color.orange()
            )
            await kanal.send(embed=e)

@bot.tree.command(name="setlog")
@app_commands.default_permissions(administrator=True)
async def setlog(interaction: discord.Interaction):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = interaction.channel.id
    await interaction.response.send_message(
        "✅ Bu kanal log kanalı olarak ayarlandı."
    )

@bot.tree.command(name="reroll")
@app_commands.default_permissions(manage_guild=True)
async def reroll(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎉 Giveaway Reroll",
        description="Yeni kazanan manuel olarak seçilebilir.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sunucu")
async def sunucu(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(
        title=f"🌍 {g.name}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="👥 Üye", value=g.member_count)
    embed.add_field(name="📅 Kuruluş", value=f"<t:{int(g.created_at.timestamp())}:D>")
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    await interaction.response.send_message(embed=embed)



bot.run(TOKEN)
