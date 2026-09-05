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

# ---------- ANNOUNCE / UPDATE MESSAGE ----------

@bot.tree.command(name="announce", description="Post an announcement/update message with an optional image")
@app_commands.describe(
    title="Title shown at the top of the message",
    message="The message content",
    image="Optional image/photo to attach",
    ping_everyone="Whether to ping @everyone",
    channel="Channel to post in (defaults to this channel)"
)
@app_commands.default_permissions(manage_messages=True)
async def announce(
    interaction: discord.Interaction,
    title: str,
    message: str,
    image: discord.Attachment = None,
    ping_everyone: bool = False,
    channel: discord.TextChannel = None
):
    target = channel or interaction.channel

    embed = discord.Embed(
        title=f"# {title}",
        description=message,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Posted by {interaction.user.display_name}")

    if image:
        embed.set_image(url=image.url)

    content = "@everyone" if ping_everyone else None
    allowed = discord.AllowedMentions(everyone=ping_everyone)

    await target.send(content=content, embed=embed, allowed_mentions=allowed)

    await interaction.response.send_message(
        f"✅ Announcement posted in {target.mention}.",
        ephemeral=True
    )

# ---------- MODERN USERINFO ----------

@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    embed = discord.Embed(
        title=f"👤 {member.display_name}",
        description="User Information",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=False)
    embed.add_field(name="🎖️ Highest Role", value=member.top_role.mention, inline=False)

    if member.joined_at:
        embed.add_field(
            name="📥 Joined",
            value=f"<t:{int(member.joined_at.timestamp())}:F>",
            inline=False
        )

    embed.add_field(
        name="📅 Account Created",
        value=f"<t:{int(member.created_at.timestamp())}:F>",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ---------- MODERN BOTINFO ----------

@bot.tree.command(name="botinfo")
async def botinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 TuffGuy Bot",
        description="Bot Statistics",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="🌍 Servers", value=len(bot.guilds))
    embed.add_field(name="👥 Users", value=len(bot.users))
    embed.add_field(name="🏓 Ping", value=f"{round(bot.latency*1000)}ms")
    await interaction.response.send_message(embed=embed)

# ---------- GIVEAWAY ----------

class GiveawayView(discord.ui.View):
    def __init__(self, winner_count, prize):
        super().__init__(timeout=None)
        self.participants = set()
        self.winner_count = winner_count
        self.prize = prize

    @discord.ui.button(label="Join", emoji="🎉", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.participants:
            await interaction.response.send_message(
                "❌ You already joined.",
                ephemeral=True
            )
            return

        self.participants.add(interaction.user.id)

        await interaction.response.send_message(
            "✅ You joined the giveaway!",
            ephemeral=True
        )

@bot.tree.command(name="giveaway")
async def giveaway(
    interaction: discord.Interaction,
    duration: str,
    winners: int,
    prize: str,
    giveaway_host: str
):

    durations = {
        "1 Hour": 3600,
        "2 Hours": 7200,
        "6 Hours": 21600,
        "12 Hours": 43200,
        "1 Day": 86400,
        "3 Days": 259200,
        "7 Days": 604800
    }

    seconds = durations.get(duration, 3600)

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description="Click the button to join!",
        color=0xFEE75C
    )

    embed.add_field(name="🏆 Prize", value=prize, inline=False)
    embed.add_field(name="⏰ Duration", value=duration)
    embed.add_field(name="🥇 Winners", value=str(winners))
    embed.set_footer(text=f"👑 {giveaway_host}")

    view = GiveawayView(winners, prize)

    await interaction.response.send_message(embed=embed, view=view)

    message = await interaction.original_response()

    await asyncio.sleep(seconds)

    if not view.participants:
        await message.reply("❌ No participants.")
        return

    winner_list = random.sample(
        list(view.participants),
        min(winners, len(view.participants))
    )

    mentions = [f"<@{x}>" for x in winner_list]

    await message.reply(
        f"🏆 Winner(s): {', '.join(mentions)}\n🎁 Prize: {prize}"
    )



# ===== EXTRA MODERN COMMANDS =====

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(title="🏓 Pong!", description=f"{round(bot.latency*1000)}ms", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dice")
async def dice(interaction: discord.Interaction):
    import random
    embed = discord.Embed(title="🎲 Dice", description=f"Result: **{random.randint(1,6)}**", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="coinflip")
async def coinflip(interaction: discord.Interaction):
    import random
    await interaction.response.send_message(embed=discord.Embed(
        title="🪙 Coin Flip",
        description=random.choice(["Heads","Tails"]),
        color=discord.Color.blurple()
    ))

@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member=None):
    member = member or interaction.user
    embed = discord.Embed(title=f"🖼️ {member.display_name}")
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kick")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason:str="Not specified"):
    await member.kick(reason=reason)
    await interaction.response.send_message(embed=discord.Embed(title="👢 Kick",description=f"{member.mention} was kicked."))

@bot.tree.command(name="ban")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason:str="Not specified"):
    await member.ban(reason=reason)
    await interaction.response.send_message(embed=discord.Embed(title="🔨 Ban",description=f"{member.mention} was banned."))

@bot.tree.command(name="clear")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount:int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🗑️ {amount} messages deleted.", ephemeral=True)





# ===== ULTRA V3 EXTRA PACK =====

@bot.tree.command(name="warn")
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    e = discord.Embed(title="⚠️ Warning", description=f"{member.mention}\nReason: {reason}", color=discord.Color.orange())
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="slowmode")
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(embed=discord.Embed(
        title="🐢 Slowmode",
        description=f"Set to {seconds} seconds.",
        color=discord.Color.blurple()
    ))

@bot.tree.command(name="lock")
@app_commands.default_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel locked.")

@bot.tree.command(name="unlock")
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel unlocked.")

@bot.tree.command(name="ship")
async def ship(interaction: discord.Interaction, member1: discord.Member, member2: discord.Member):
    import random
    percentage = random.randint(1,100)
    await interaction.response.send_message(embed=discord.Embed(
        title="❤️ Ship",
        description=f"{member1.mention} × {member2.mention}\nCompatibility: %{percentage}",
        color=discord.Color.red()
    ))

@bot.tree.command(name="8ball")
async def eightball(interaction: discord.Interaction, question: str):
    import random
    answers = ["Yes","No","Maybe","Definitely","I doubt it"]
    await interaction.response.send_message(embed=discord.Embed(
        title="🎱 8Ball",
        description=random.choice(answers),
        color=discord.Color.dark_purple()
    ))





# ===== ULTRA V5 SYSTEMS =====

# Simple ticket panel
class TicketView(discord.ui.View):
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites
        )
        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

@bot.tree.command(name="ticketpanel")
@app_commands.default_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Support System",
        description="Click the button to open a ticket.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

# Simple help menu
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General"),
            discord.SelectOption(label="Moderation"),
            discord.SelectOption(label="Fun"),
        ]
        super().__init__(placeholder="Select a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"📂 Selected category: {self.values[0]}",
            ephemeral=True
        )

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

@bot.tree.command(name="helpv2")
async def helpv2(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Select a category below.",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=HelpView())

# Auto-role (lightweight version)
AUTOROLE_ID = None

@bot.event
async def on_member_join(member):
    if AUTOROLE_ID:
        role = member.guild.get_role(AUTOROLE_ID)
        if role:
            await member.add_roles(role)





# ===== ULTRA V6 EXTRAS =====

LOG_CHANNEL_ID = None  # log channel ID

@bot.event
async def on_member_remove(member):
    if LOG_CHANNEL_ID:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            e = discord.Embed(
                title="👋 Member Left",
                description=f"{member} left the server.",
                color=discord.Color.red()
            )
            await channel.send(embed=e)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if LOG_CHANNEL_ID:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            e = discord.Embed(
                title="🗑️ Message Deleted",
                description=message.content[:1000] or "No content",
                color=discord.Color.orange()
            )
            await channel.send(embed=e)

@bot.tree.command(name="setlog")
@app_commands.default_permissions(administrator=True)
async def setlog(interaction: discord.Interaction):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = interaction.channel.id
    await interaction.response.send_message(
        "✅ This channel has been set as the log channel."
    )

@bot.tree.command(name="reroll")
@app_commands.default_permissions(manage_guild=True)
async def reroll(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎉 Giveaway Reroll",
        description="A new winner can be selected manually.",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="server")
async def server(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(
        title=f"🌍 {g.name}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="👥 Members", value=g.member_count)
    embed.add_field(name="📅 Created", value=f"<t:{int(g.created_at.timestamp())}:D>")
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    await interaction.response.send_message(embed=embed)




# ===== ULTRA V7 =====
invite_cache = {}

@bot.event
async def on_ready():
    try:
        for guild in bot.guilds:
            invite_cache[guild.id] = await guild.invites()
    except:
        pass
    print(f"{bot.user} is active!")

@bot.tree.command(name="invites")
async def invites(interaction: discord.Interaction, member: discord.Member=None):
    member = member or interaction.user
    await interaction.response.send_message(
        embed=discord.Embed(
            title="📨 Invite Info",
            description=f"Invite statistics for {member.mention} coming soon.",
            color=discord.Color.blurple()
        )
    )

@bot.event
async def on_member_join(member):
    inviter = "Unknown"
    try:
        old = invite_cache.get(member.guild.id, [])
        new = await member.guild.invites()

        for inv in new:
            for o in old:
                if inv.code == o.code and inv.uses > o.uses:
                    inviter = str(inv.inviter)
                    break

        invite_cache[member.guild.id] = new
    except:
        pass

    embed = discord.Embed(
        title="👋 Welcome",
        description=f"Member: {member.mention}\nInvited by: **{inviter}**\nTotal Members: **{member.guild.member_count}**",
        color=discord.Color.green()
    )

    if LOG_CHANNEL_ID:
        ch = bot.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)

@bot.tree.command(name="closeticket")
async def closeticket(interaction: discord.Interaction):
    if interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("🔒 Closing ticket...")
        await interaction.channel.delete()

bot.run(TOKEN)
