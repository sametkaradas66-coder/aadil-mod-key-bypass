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

bot.run(TOKEN)
