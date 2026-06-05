import discord
from discord.ext import commands
import random
import asyncio
import os
import aiohttp
import yt_dlp
import datetime

# Configuration variables
TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIX = "!"
WELCOME_CHANNEL_NAME = "genel"
AI_CHAT_CHANNEL_NAME = "tuffai-sohbet"

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Bot connected successfully as: {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name=f"{PREFIX}yardım"))

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if channel:
        embed = discord.Embed(
            title=f"Welcome, {member.name}!",
            description=f"Welcome to the **{member.guild.name}** server!\nHave a great time here 🎉",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"The server now has {member.guild.member_count} members!")
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.TextChannel) and message.channel.name == AI_CHAT_CHANNEL_NAME:
        if message.content.startswith(PREFIX):
            await bot.process_commands(message)
            return

        async with message.channel.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.lolhuman.xyz/api/openai?apikey=free&text={message.content}") as resp:
                        reply_text = await resp.text()
                        embed = discord.Embed(
                            title="🤖 TuffAI Response",
                            description=reply_text[:4000],
                            color=discord.Color.blurple()
                        )
                        embed.set_footer(text=f"Asked by: {message.author}")
                        await message.reply(embed=embed)
                        return
            except Exception:
                await message.reply("❌ TuffAI is currently unavailable, please try again later.")
                return

    await bot.process_commands(message)

@bot.command(name="yardım", aliases=["yardim", "help"])
async def yardim(ctx):
    embed = discord.Embed(title="📋 Bot Commands", color=discord.Color.blurple())
    embed.add_field(name="🛡️ Moderation", value="`!ban` `!kick` `!mute` `!unmute` `!uyar` `!temizle`", inline=False)
    embed.add_field(name="🎵 Music", value="`!çal` `!dur` `!devam` `!atla` `!ses` `!çık`", inline=False)
    embed.add_field(name="🎮 Games", value="`!zar` `!yazıtura` `!tahmin` `!trivia` `!8top`", inline=False)
    embed.add_field(name="🎉 Giveaways", value="`!çekiliş <minutes> <winners> <tr/en> <prize>`", inline=False)
    embed.add_field(name="📊 Polls", value='`!anket "Question?" "Option A" "Option B"` | `!anketkapat <message_id>`', inline=False)
    embed.add_field(name="🤖 TuffAI Chat", value=f"`!sor <question>` or type directly inside the `#{AI_CHAT_CHANNEL_NAME}` channel", inline=False)
    embed.add_field(name="ℹ️ Info", value="`!ping` `!sunucu` `!kullanıcı`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Ban", description=f"**{member}** has been banned.\nReason: {reason}", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Kick", description=f"**{member}** has been kicked.\nReason: {reason}", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int = 10, *, reason="No reason provided"):
    duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="🔇 Mute", description=f"**{member}** has been muted for {minutes} minutes.\nReason: {reason}", color=discord.Color.yellow())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    embed = discord.Embed(title="🔊 Unmute", description=f"Mute restriction lifted for **{member}**.", color=discord.Color.green())
    await ctx.send(embed=embed)

warnings_database = {}

@bot.command()
@commands.has_permissions(kick_members=True)
async def uyar(ctx, member: discord.Member, *, reason="No reason provided"):
    uid = str(member.id)
    warnings_database[uid] = warnings_database.get(uid, 0) + 1
    embed = discord.Embed(title="⚠️ Warning", description=f"**{member}** has been warned! (Total: {warnings_database[uid]})\nReason: {reason}", color=discord.Color.gold())
    await ctx.send(embed=embed)
    if warnings_database[uid] >= 3:
        await member.kick(reason="Reached 3 warnings limit")
        await ctx.send(f"🚨 {member} has been kicked automatically for reaching 3 warnings!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def temizle(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑️ Cleaned {amount} messages.")
    await asyncio.sleep(3)
    await msg.delete()

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
        return info['url'], info.get('title', 'Unknown Title')

async def play_next(ctx):
    gid = ctx.guild.id
    if gid in music_queue and music_queue[gid]:
        query, title = music_queue[gid].pop(0)
        current_song[gid] = title
        url, title = await asyncio.get_event_loop().run_in_executor(None, get_audio_url, query)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTS)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(embed=discord.Embed(title="🎵 Now Playing", description=title, color=discord.Color.purple()))

@bot.command(name="çal", aliases=["cal", "play"])
async def cal(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("❌ You must join a voice channel first!")
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    gid = ctx.guild.id
    if gid not in music_queue:
        music_queue[gid] = []

    if ctx.voice_client.is_playing():
        music_queue[gid].append((query, query))
        await ctx.send(f"➕ Added to queue: **{query}**")
    else:
        music_queue[gid].insert(0, (query, query))
        await play_next(ctx)

@bot.command(name="dur", aliases=["pause"])
async def dur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused.")

@bot.command(name="devam", aliases=["resume"])
async def devam(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed.")

@bot.command(name="atla", aliases=["skip"])
async def atla(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped.")

@bot.command(name="ses", aliases=["volume", "vol"])
async def ses(ctx, level: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)
        ctx.voice_client.source.volume = level / 100
        await ctx.send(f"🔊 Volume set to: {level}%")

@bot.command(name="çık", aliases=["cik", "leave", "dc"])
async def cik(ctx):
    if ctx.voice_client:
        music_queue[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")

giveaways_database = {}

LANG_PACKS = {
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

class GiveawayButtonView(discord.ui.View):
    def __init__(self, message_id, lang_code="tr"):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.lang_code = lang_code
        self.join_button.label = LANG_PACKS[lang_code]["join_btn"]

    @discord.ui.button(label="🎟️ Join", style=discord.ButtonStyle.green, custom_id="giveaway_join_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = LANG_PACKS[self.lang_code]
        if self.message_id not in giveaways_database:
            return await interaction.response.send_message("❌", ephemeral=True)
        data = giveaways_database[self.message_id]
        uid = interaction.user.id
        if uid in data["participants_list"]:
            return await interaction.response.send_message(lang["already"], ephemeral=True)
        data["participants_list"].add(uid)
        await interaction.response.send_message(lang["joined"], ephemeral=True)
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name=f"👥 {lang['participants']}", value=str(len(data["participants_list"])), inline=True)
        await interaction.message.edit(embed=embed)

@bot.command(name="çekiliş", aliases=["cekilisbaslat", "giveaway"])
@commands.has_permissions(manage_guild=True)
async def cekilisbaslat(ctx, duration_minutes: int, winners_count: int, lang_code: str = "tr", *, prize_text: str):
    if lang_code not in LANG_PACKS:
        lang_code = "tr"
    lang = LANG_PACKS[lang_code]
    end_timestamp = discord.utils.utcnow().timestamp() + duration_minutes * 60

    embed = discord.Embed(title=lang["title"], color=discord.Color.gold())
    embed.add_field(name=f"🎁 {lang['prize']}", value=prize_text, inline=False)
    embed.add_field(name=f"⏱️ {lang['duration']}", value=f"{duration_minutes} {lang['min_unit']}", inline=True)
    embed.add_field(name=f"🏆 {lang['winner_count']}", value=str(winners_count), inline=True)
    embed.add_field(name=f"👥 {lang['participants']}", value="0", inline=True)
    embed.set_footer(text=lang["footer"])
    embed.timestamp = discord.utils.utcnow()

    view = GiveawayButtonView(None, lang_code)
    msg = await ctx.send(embed=embed, view=view)
    view.message_id = msg.id

    giveaways_database[msg.id] = {
        "participants_list": set(),
        "winners_count": winners_count,
        "end_timestamp": end_timestamp,
        "lang_code": lang_code,
        "text_channel": ctx.channel,
        "prize_text": prize_text,
        "msg_object": msg,
    }

    await asyncio.sleep(duration_minutes * 60)

    data = giveaways_database.pop(msg.id, None)
    if not data:
        return
    lang = LANG_PACKS[data["lang_code"]]
    final_list = list(data["participants_list"])
    if not final_list:
        winners_mention_string = lang["no_winner"]
    else:
        selected_winners = random.sample(final_list, min(data["winners_count"], len(final_list)))
        winners_mention_string = " ".join(f"<@{u}>" for u in selected_winners)

    embed2 = discord.Embed(title=lang["ended"], color=discord.Color.red())
    embed2.add_field(name=f"🎁 {lang['prize']}", value=data["prize_text"], inline=False)
    embed2.add_field(name=f"🏆 {lang['winners']}", value=winners_mention_string, inline=False)
    embed2.timestamp = discord.utils.utcnow()
    await data["msg_object"].edit(embed=embed2, view=None)
    await data["text_channel"].send(f"🎉 {lang['ended']} | {lang['prize']}: **{data['prize_text']}** | {lang['winners']}: {winners_mention_string}")

polls_database = {}

class PollButtonView(discord.ui.View):
    def __init__(self, message_id, options_list):
        super().__init__(timeout=None)
        for i, option in enumerate(options_list[:5]):
            indicators = ["🅰️", "🅱️", "🇨", "🇩", "🇪"]
            btn = discord.ui.Button(
                label=option[:60],
                style=discord.ButtonStyle.primary,
                emoji=indicators[i],
                custom_id=f"poll_{message_id}_{i}"
            )
            btn.callback = self.create_vote_callback(i)
            self.add_item(btn)

    def create_vote_callback(self, index):
        async def vote_callback(interaction: discord.Interaction):
            msg_id = interaction.message.id
            if msg_id not in polls_database:
                return await interaction.response.send_message("❌ Poll not found.", ephemeral=True)
            data = polls_database[msg_id]
            uid = interaction.user.id
            if uid in data["voters_tracker"]:
                old_index = data["voters_tracker"][uid]
                data["votes_counter"][old_index] -= 1
            data["voters_tracker"][uid] = index
            data["votes_counter"][index] += 1
            total_votes = sum(data["votes_counter"])
            embed = interaction.message.embeds[0]
            embed.clear_fields()
            for i, opt in enumerate(data["options_list"]):
                votes_count = data["votes_counter"][i]
                percentage = (votes_count / total_votes * 100) if total_votes > 0 else 0
                visual_bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
                embed.add_field(
                    name=f"{'🅰️🅱️🇨🇩🇪'[i*2:i*2+2] if i < 2 else ['🇨','🇩','🇪'][i-2]} {opt}",
                    value=f"`{visual_bar}` {votes_count} votes ({percentage:.1f}%)",
                    inline=False
                )
            embed.set_footer(text=f"Total votes: {total_votes} | You can change your choice")
            await interaction.message.edit(embed=embed)
            await interaction.response.send_message(f"✅ Registered vote for: **{data['options_list'][index]}**!", ephemeral=True)
        return vote_callback

@bot.command(name="anket")
async def anket(ctx, question: str, *options):
    if len(options) < 2:
        return await ctx.send("❌ Enter at least 2 options!\nUsage: `!anket \"Question?\" \"Option 1\" \"Option 2\"`")
    if len(options) > 5:
        return await ctx.send("❌ You can enter at most 5 options!")

    embed = discord.Embed(title=f"📊 {question}", color=discord.Color.blue())
    votes_counter = [0] * len(options)
    indicators = ["🅰️", "🅱️", "🇨", "🇩", "🇪"]
    for i, opt in enumerate(options):
        embed.add_field(
            name=f"{indicators[i]} {opt}",
            value="`░░░░░░░░░░` 0 votes (0.0%)",
            inline=False
        )
    embed.set_footer(text="Total votes: 0 | You can change your choice")
    embed.set_author(name=f"Poll by: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

    msg = await ctx.send(embed=embed)

    polls_database[msg.id] = {
        "question": question,
        "options_list": list(options),
        "votes_counter": votes_counter,
        "voters_tracker": {},
    }

    view = PollButtonView(msg.id, list(options))
    await msg.edit(view=view)

@bot.command(name="anketbitter", aliases=["anketkapat"])
@commands.has_permissions(manage_guild=True)
async def anketkapat(ctx, message_id: int):
    if message_id not in polls_database:
        return await ctx.send("❌ No active poll found with that ID.")
    data = polls_database.pop(message_id)
    total_votes = sum(data["votes_counter"])
    embed = discord.Embed(title=f"📊 [CLOSED] {data['question']}", color=discord.Color.red())
    winning_index = data["votes_counter"].index(max(data["votes_counter"])) if total_votes > 0 else None
    for i, opt in enumerate(data["options_list"]):
        votes_count = data["votes_counter"][i]
        percentage = (votes_count / total_votes * 100) if total_votes > 0 else 0
        visual_bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        trophy_suffix = " 🏆" if i == winning_index and total_votes > 0 else ""
        embed.add_field(
            name=f"{opt}{trophy_suffix}",
            value=f"`{visual_bar}` {votes_count} votes ({percentage:.1f}%)",
            inline=False
        )
    embed.set_footer(text=f"Total votes: {total_votes} | Poll concluded.")
    await ctx.send(embed=embed)

@bot.command()
async def zar(ctx, amount: int = 1, faces: int = 6):
    results = [random.randint(1, faces) for _ in range(min(amount, 10))]
    await ctx.send(f"🎲 **{', '.join(map(str, results))}** (Total: {sum(results)})")

@bot.command(name="yazıtura", aliases=["yazitura", "flip"])
async def yazıtura(ctx):
    outcome = random.choice(["🪙 Heads", "🪙 Tails"])
    await ctx.send(outcome)

number_guessing_sessions = {}

@bot.command()
async def tahmin(ctx):
    if ctx.channel.id in number_guessing_sessions:
        return await ctx.send("⚠️ An active game session is already running in this channel!")
    secret_number = random.randint(1, 100)
    number_guessing_sessions[ctx.channel.id] = secret_number
    await ctx.send("🔢 I am thinking of a number between 1 and 100! Guess using `!say <number>`.")

@bot.command()
async def say(ctx, guess: int):
    if ctx.channel.id not in number_guessing_sessions:
        return await ctx.send("❌ No active game. Start one using `!tahmin`.")
    secret = number_guessing_sessions[ctx.channel.id]
    if guess < secret:
        await ctx.send("📈 Higher!")
    elif guess > secret:
        await ctx.send("📉 Lower!")
    else:
        del number_guessing_sessions[ctx.channel.id]
        await ctx.send(f"🎉 **{ctx.author.mention} guessed correctly! The number was {secret}!**")

trivia_questions_list = [
    ("What is the capital city of Turkey?", "Ankara"),
    ("What is the largest ocean on Earth?", "Pacific"),
    ("In which year was Python created?", "1991"),
    ("In which year was Discord founded?", "2015"),
    ("What is the largest planet in our solar system?", "Jupiter"),
    ("What is the chemical formula for water?", "H2O"),
    ("How many provinces are there in Turkey?", "81"),
]

@bot.command()
async def trivia(ctx):
    question, answer = random.choice(trivia_questions_list)
    embed = discord.Embed(title="🧠 Trivia", description=question, color=discord.Color.teal())
    embed.set_footer(text="Answer within 30 seconds!")
    await ctx.send(embed=embed)

    def check_message(m):
        return m.channel == ctx.channel and not m.a
