import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from discord.utils import escape_mentions, escape_markdown
import random
import re
import asyncio

# Load .env token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Setup bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="<",
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

sniped_messages = {}

# ---------------------------
# EVENTS
# ---------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    try:
        if message.content.startswith('<echo'):
            await message.delete()
            text_to_echo = message.content[len('<echo'):].strip()
            if text_to_echo:
                await message.channel.send(text_to_echo)
    except Exception as e:
        print(f"[on_message error] {e}")

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }

    await asyncio.sleep(60)
    if sniped_messages.get(message.channel.id) and sniped_messages[message.channel.id]["content"] == message.content:
        del sniped_messages[message.channel.id]

# ---------------------------
# COMMANDS
# ---------------------------

@bot.command(help="Greets the user")
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}!")

@bot.command(help="Checks if the bot is running")
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command(help="Wrong bot, check out the one literally called Chat Revival Bot")
async def revive(ctx):
    await ctx.send("Sorry but I won't steal the jobs of my fellow bots, unless it's RNGesus, screw that guy.")
    
@bot.command(help="IS THAT A SURVIV REFERENCE??")
async def reviv(ctx):
    await ctx.send("Not only did you make a typo, but you also used the wrong prefix, AND you also referenced Surviv.")

@bot.command(help="yvlis")
async def mango(ctx):
    await ctx.send("🍋")

@bot.command(help="silvy")
async def lemon(ctx):
    await ctx.send("🥭")

@bot.command(help="99% OF GAMBLERS QUIT BEFORE THEY HIT BIG")
async def gamble(ctx):
    symbols = ["🥭", "🍋", "🥝", "0️⃣", "💀", "⭐", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    slot_display = " | ".join(result)

    if result.count(result[0]) == 3:
        response = f"🎉 JACKPOT! {slot_display} - You win big!"
    elif len(set(result)) == 2:
        response = f"So close! {slot_display} - You almost had it."
    else:
        response = f"{slot_display} - Better luck next time."

    await ctx.send(response)

@bot.command(help="Choose between words or roll a number (e.g. <roll 10 or <roll red, blue)")
async def roll(ctx, *, args):
    async def replace_mentions(text):
        mention_pattern = r'<@!?(\d+)>'

        async def replace(match):
            user_id = int(match.group(1))
            member = ctx.guild.get_member(user_id) if ctx.guild else None
            if member:
                return f"@{member.display_name}"
            try:
                user = await bot.fetch_user(user_id)
                return f"@{user.name}"
            except discord.NotFound:
                return "@unknown"

        parts = []
        last_end = 0
        for match in re.finditer(mention_pattern, text):
            parts.append(text[last_end:match.start()])
            parts.append(await replace(match))
            last_end = match.end()
        parts.append(text[last_end:])
        return ''.join(parts)

    cleaned_args = await replace_mentions(args)

    if ',' in cleaned_args:
        choices = [choice.strip() for choice in cleaned_args.split(",") if choice.strip()]
        if len(choices) >= 2:
            result = random.choice(choices)
            await ctx.send(f"🎲 You rolled: {result}")
        else:
            await ctx.send("❌ Please provide at least two comma-separated choices.")
        return

    parts = cleaned_args.strip().split()
    if parts:
        try:
            upper = int(parts[0])
            if upper <= 0:
                await ctx.send("❌ Please enter a number greater than 0.")
                return
            result = random.randint(1, upper)
            await ctx.send(f"🎲 You rolled: {result}")
            return
        except ValueError:
            pass

    await ctx.send("❌ Usage:\n- `<roll 100` → random number from 1–100\n- `<roll red, blue, green` → pick from choices")

@bot.command(help="Snipes the most recently deleted message in this channel")
async def snipe(ctx):
    snipe_data = sniped_messages.get(ctx.channel.id)

    if snipe_data:
        time_diff = (discord.utils.utcnow() - snipe_data["time"]).seconds
        await ctx.send(
            f"Deleted message by **{snipe_data['author']}** ({time_diff} seconds ago):\n> {snipe_data['content']}"
        )
    else:
        await ctx.send("There's nothing to snipe, stop being paranoid lmao")

@bot.command(help="Who'll be 'pinged' this time?")
async def pingroulette(ctx):
    options = [
        ("ping ping tolerance level 4", "<:gamma_brilliant:1363827439146635376>"),
        ("don't ping", "<:hyper_brilliant:1363720885244006533>"),
        ("ping myself", "<:super_brilliant:1363720901702451270>"),
        ("ping kan", "<:brilliant:1363720913253699615>"),
        ("ping blundy", "<:great:1363720926264557709>"),
        ("ping kk", "<:excellent:1363720953217024031>"),
        ("ping tampy", "<:good:1363720964810080316>"),
        ("ping silvy", "<:inaccuracy:1363721001774612621>"),
        ("ping erix", "<:mistake:1363721029377327294>"),
        ("ping no one", "<:blunder:1363721040890560572>"),
        ("Ping Amg.", "<:super_blunder:1363721054949998792>"),
        ("ping here", "<:hyper_blunder:1363721067893358675>"),
        ("ping everyone", "<:gamma_blunder:1363728794019696701>"),
        ("cheeseburger", "🍔")
    ]

    label, emoji = random.choice(options)

    # First message (RNGesus style)
    await ctx.send(f":game_die: {label} {emoji}")

    # Second message (Dyno fake ping style)
    fake_ping = "@\u200b" + label
    await ctx.send(fake_ping)

@bot.command(help="Ask the all-knowing 8-ball a question")
async def eightball(ctx, *, question: str = None):
    responses = [
        "Yes.", "No.", "Maybe.", "Absolutely.", "Definitely not.",
        "Ask again later.", "OUT OF ALL THE QUESTIONS YOU CAN ASK, YOU ASK THAT??",
        "Without a doubt.", "I wouldn’t count on it.",
        "99% sure it’s yes.", "Try again after touching grass."
    ]

    if not question:
        await ctx.send("🎱 You need to ask a question. Example: `<8ball will i get pinged`")
        return

    answer = random.choice(responses)
    await ctx.send(f"🎱 {answer}")

@bot.command(help="Rates anything from 1/10 to 100/10")
async def rate(ctx, *, thing: str = None):
    if not thing:
        await ctx.send("📊 Rate what? Example: `<rate Blundy's habit of reacting in the shadows.`")
        return

    score = random.choice(
        list(range(1, 11)) + [69, 100, 0, -1, 404, 456]  # Spice it up
    )
    await ctx.send(f"📊 I'd rate **{thing}** a solid **{score}/10**")

@bot.command(help="Mocks your sentence. Example: `<mock I am serious`")
async def mock(ctx, *, text: str = None):
    if not text:
        await ctx.send("What do you want me to mock? Example: `<mock you always say that`")
        return

    mocked = ''.join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )
    await ctx.send(f"{mocked}")

# ---------------------------
# Run bot
# ---------------------------

bot.run(TOKEN)

