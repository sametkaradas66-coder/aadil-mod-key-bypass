import discord
from discord.ext import commands
import requests
import json
import os

DISCORD_TOKEN = "BURAYA_DISCORD_TOKEN"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SETTINGS_FILE = "kanallar.json"

def load_data():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

kanallar = load_data()

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kanal(ctx, channel: discord.TextChannel):

    kanallar[str(ctx.guild.id)] = channel.id
    save_data(kanallar)

    await ctx.send(
        f"✅ AI sohbet kanalı ayarlandı: {channel.mention}"
    )

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    guild_id = str(message.guild.id)

    if guild_id in kanallar:

        if message.channel.id == kanallar[guild_id]:

            try:

                msg = await message.reply("🧠 düşünüyorum...")

                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": message.content,
                        "stream": False
                    }
                )

                cevap = response.json()["response"]

                await msg.delete()

                if len(cevap) > 2000:
                    for i in range(0, len(cevap), 2000):
                        await message.channel.send(
                            cevap[i:i+2000]
                        )
                else:
                    await message.channel.send(cevap)

            except Exception as e:
                await message.channel.send(
                    f"Hata: {e}"
                )

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
