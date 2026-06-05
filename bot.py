import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai
import json
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

SETTINGS_FILE = "kanallar.json"

def load_data():
    if os.path.exists(SETTINGS_FILE):
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    return {}

def save_data(data):
    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

kanallar = load_data()

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kanal(
    ctx,
    channel: discord.TextChannel
):
    kanallar[str(ctx.guild.id)] = channel.id

    save_data(kanallar)

    await ctx.send(
        f"✅ AI sohbet kanalı ayarlandı: {channel.mention}"
    )

@bot.command()
async def ping(ctx):
    await ctx.send(
        f"🏓 {round(bot.latency * 1000)}ms"
    )

@bot.command()
async def yazitura(ctx):
    import random

    await ctx.send(
        f"🪙 {random.choice(['Yazı','Tura'])}"
    )

@bot.command()
async def zar(ctx):
    import random

    await ctx.send(
        f"🎲 {random.randint(1,6)}"
    )

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if not message.guild:
        return

    guild_id = str(message.guild.id)

    if guild_id in kanallar:

        if message.channel.id == kanallar[guild_id]:

            thinking = await message.reply(
                "🧠 düşünüyorum..."
            )

            try:

                prompt = f"""
Kullanıcı: {message.content}

Kısa, samimi ve Türkçe cevap ver.
"""

                response = model.generate_content(
                    prompt
                )

                cevap = response.text

                await thinking.delete()

                if len(cevap) > 2000:

                    for i in range(
                        0,
                        len(cevap),
                        1900
                    ):
                        await message.channel.send(
                            cevap[i:i+1900]
                        )

                else:
                    await message.channel.send(
                        cevap
                    )

            except Exception as e:

                await thinking.edit(
                    content=f"❌ Hata: {e}"
                )

    await bot.process_commands(
        message
    )

bot.run(TOKEN)
