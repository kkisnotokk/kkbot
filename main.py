import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from discord.utils import escape_mentions, escape_markdown
import random
import re
import asyncio
import aiohttp

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
rigged_responses = {}

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

    ctx = await bot.get_context(message)

    # Intercept for rigging
    if ctx.valid and message.author.id in rigged_responses:
        response = rigged_responses.pop(message.author.id)
        await message.channel.send(f"🎯 {response}")
        return  # Skip running original command

    # Manually handle <echo
    try:
        if message.content.startswith('<echo'):
            await message.delete()
            text_to_echo = message.content[len('<echo'):].strip()
            if text_to_echo:
                await message.channel.send(text_to_echo)
    except Exception as e:
        print(f"[on_message error] {e}")

    # Let other commands work as normal
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
    
@bot.command(help="it's vivid")
async def vivid(ctx):
    await ctx.send("Holy shit is it time for another vividstory? I better make sure my kids don't see this.")

@bot.command(help="nothing")
async def nothing(ctx):
    await ctx.send("")

@bot.command(help="pew pew")
async def sniper(ctx):
    await ctx.send("Yes hello I'm here what do you need?")

@bot.command(help="Rick, clip that")
async def threesixtynoscope(ctx):
    await ctx.send("https://tenor.com/view/360noscope-gif-18161400")

@bot.command(help="It's kk")
async def kk(ctx):
    await ctx.send("...is not okk")

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
    rigged = rigged_responses.pop(ctx.author.id, None)
    if rigged:
        await ctx.send(f"🎯 {rigged}")
        return

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
            
    await ctx.send("❌ Usage:\n- <roll 100 → random number from 1–100\n- <roll red, blue, green → pick from choices")

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

    # First message (RNGesus-style)
    await ctx.send(f":game_die: {label} {emoji}")

    # Second message (Dyno-style fake ping)
    fake_ping = f"{label}".replace("ping ", "")  # strips "ping " to make it look like a name
    fake_ping = "@" + "\u200b".join(fake_ping)     # Inserts zero-width space to prevent real ping
    await ctx.send(fake_ping)

@bot.command(help="Ask the all-knowing 8-ball a question")
async def eightball(ctx, *, question: str = None):
    rigged = rigged_responses.pop(ctx.author.id, None)
    if rigged:
        await ctx.send(f"🎯 {rigged}")
        return

    responses = [
        "Maybe.", "Absolutely.", "Absolutely not.",
        "Ask again in exactly 69.42 seconds.", "You have better things to worry about :3 (you don't wanna know)",
        "Without a doubt.", "I wouldn’t count on it.",
        "I'm tired of your dumb questions, go ask Emilybot.", "Try again after touching grass.", "You really don't want me to answer that",
        "Idk ask Emilybot.", "All will be clear soon, wait, no it won't I lied you're cooked.",
        f"It's ggs {ctx.author.name}, you know the answer.", "Er uh you don't need to know that.",
        "I am not answering that.", "Shut up I'm busy getting drunk.",
        "@kk there's been an error, I think I ran out of shits to give.", "(Sponsored) We are sorry to interupt this command but we must inform you of the hot new bot on the market— @IBM!! You should use '@IBM coin' and try it now!!"
    ]

    if not question:
        await ctx.send("🎱 You need to ask a question. Example: <8ball will i get pinged")
        return

    answer = random.choice(responses)
    await ctx.send(f"🎱 {answer}")

@bot.command(help="Rates anything from 1/10 to 100/10")
async def rate(ctx, *, thing: str = None):
    rigged = rigged_responses.pop(ctx.author.id, None)
    if rigged:
        await ctx.send(f"🎯 {rigged}")
        return

    if not thing:
        await ctx.send("📊 Rate what? Example: <rate Blundy's habit of reacting in the shadows.")
        return

    score = random.choice(
        list(range(1, 11)) + [69, 100, 0, -1, 404, 456]  # Spice it up
    )
    
    await ctx.send(f"📊 I'd rate **{thing}** a solid **{score}/10**")

@bot.command(help="Mocks your sentence. Example: <mock I am serious")
async def mock(ctx, *, text: str = None):
    if not text:
        await ctx.send("What do you want me to mock? Example: <mock you always say that")
        return

    mocked = ''.join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )
    await ctx.send(f"{mocked}")

@bot.command(help="Rig your next <roll, <eightball, or <rate response to say what you want.")
async def rig(ctx, *, message: str):
    rigged_responses[ctx.author.id] = message
    await ctx.send(f":3 Your next command is rigged to say: `{message}`")

@bot.command()
async def remind(ctx, time: str, *, task: str = None):
    """Set a reminder. Usage: <remind <time> [optional task]"""
    
    unit = time[-1]
    if not time[:-1].isdigit() or unit not in ['s', 'm', 'h']:
        await ctx.send("Invalid time format. Use something like `10s`, `5m`, or `24h`.")
        return

    amount = int(time[:-1])
    if unit == 's':
        seconds = amount
    elif unit == 'm':
        seconds = amount * 60
    elif unit == 'h':
        seconds = amount * 3600

    await ctx.send(f"Okk {ctx.author.mention}, I'll remind you in {amount}{unit}.")

    await asyncio.sleep(seconds)

    if task:
        await ctx.send(f"WEWOWEWOWEWO {ctx.author.mention}: {task}")
    else:
        await ctx.send(f"Reminder for {ctx.author.mention}!")

@bot.command()
async def define(ctx, *, word: str):
    """
    Looks up the definition of a word using Free Dictionary API.
    Usage: <define example
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await ctx.send(f"❌ No definition found for **{word}**.")
                return
            
            data = await response.json()

    try:
        meaning = data[0]["meanings"][0]
        part_of_speech = meaning["partOfSpeech"]
        definition = meaning["definitions"][0]["definition"]
        example = meaning["definitions"][0].get("example", None)

        msg = f"**{word.capitalize()}** (*{part_of_speech}*)\n{definition}"
        if example:
            msg += f"\n*Example:* {example}"
        
        await ctx.send(msg)

    except (KeyError, IndexError):
        await ctx.send(f"❌ Could not parse definition for **{word}**.")

# ---
# Code Merged from Another bot
# ---

# --- Button Views ---

class BoardRepresentationButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Read about the first part - Board Representation", style=discord.ButtonStyle.success)
    async def go_to_boardrepresentation(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("boardrepresentation")
        await command.invoke(ctx)

class EvaluationButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Done reading? You may want to know about evaluating too", style=discord.ButtonStyle.success)
    async def go_to_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("evaluation")
        await command.invoke(ctx)

class MinimaxButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="You might want to read about Minimax too", style=discord.ButtonStyle.success)
    async def go_to_minimax(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("minimax")
        await command.invoke(ctx)

class AlphaBetaButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="You might also want to optimize Minimax", style=discord.ButtonStyle.success)
    async def go_to_alphabeta(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("alphabeta")
        await command.invoke(ctx)

class MoveOrderingButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Optimize Alpha-Beta pruning", style=discord.ButtonStyle.success)
    async def go_to_moveordering(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("moveordering")
        await command.invoke(ctx)

class TranspositionTableButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Save even more searching time?", style=discord.ButtonStyle.success)
    async def go_to_transpositiontable(self, interaction: discord.Interaction, button: discord.ui.Button):
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("transpositiontable")
        await command.invoke(ctx)

# --- Chess Engine Tutorial Commands ---

@bot.command(name="chess_engine_tutorial", help="Getting started with writing a chess engine")
async def chessenginetutorial(ctx):
    await ctx.send("""
Writing a chess engine is a lot of work, but it can be a fun and rewarding project.
If you are new, you can start with a library. I will use the `python-chess` package here. https://python-chess.readthedocs.io for more info.

There are 3 main parts of a chess engine:
1. The board representation
2. The board evaluation
3. The search algorithm
""", view=BoardRepresentationButton(ctx.bot))

@bot.command(name="boardrepresentation", help="A brief documentation about board representation")
async def boardrepresentation(ctx):
    await ctx.send("""
With `python-chess` it's quite easy to represent a chessboard. There is a built-in `Board` class with all the rules of chess and a `unicode()` method for displaying an Unicode board.
Here is an example about how to use it:
```py
import chess

board = chess.Board()
print(board.unicode(
# These are the optional parameters you can use for your board
invert_color=True, # Invert the color of the black pieces
borders=False, # Shows borders around the board
empty_square=".", # The character for empty squares
orientation=chess.WHITE # The orientation of the board
))
Once you are done, continue with the second part - evaluation.
""", view=EvaluationButton(ctx.bot))

@bot.command(name="evaluation", help="A brief documentation about board evaluation")
async def evaluation(ctx):
    await ctx.send("You can read about a simple evaluation function here: https://docs.google.com/document/d/1ZSZdRZMz72WQPmbPRlrE3xMOSmRajyhjcLlWwhb_Mdc/edit?usp=sharing", view=MinimaxButton(ctx.bot))

@bot.command(name="minimax", help="A brief documentation about the minimax algorithm")
async def minimax(ctx):
    await ctx.send("You can read about the explanation of minimax here: https://docs.google.com/document/d/1f6Xrm-6T2NAjBnnoDXRhdUJLl3NmTY_nEJXXtDP1Q4c/edit?usp=sharing", view=AlphaBetaButton(ctx.bot))

@bot.command(name="alphabeta", help="A brief documentation about alpha-beta pruning")
async def alphabeta(ctx):
    await ctx.send("You can read about the explanation of alpha-beta pruning here: https://docs.google.com/document/d/1ePVT1ep_WX5m-qG2-5rRW_PvSVsZXlqix-fE7Z3frRE/edit?usp=sharing", view=MoveOrderingButton(ctx.bot))

@bot.command(name="moveordering", help="A brief documentation about move ordering")
async def moveordering(ctx):
    await ctx.send("Have a headache here: https://docs.google.com/document/d/1e-Q-mv8ctG9rGn-806Jfb4u9p3K8iAJiCbGEL7vjHkk/edit?usp=sharing", view=TranspositionTableButton(ctx.bot))

@bot.command(name="transpositiontable", help="A brief documentation about transposition tables")
async def transpositiontable(ctx):
    await ctx.send("Read about transposition tables here: https://docs.google.com/document/d/1eI1TK_9bX9VKk6ss9tGDD4LfmJB3vmOVRRYV2FjijAY/edit?usp=sharing")

# ---------------------------
# Run bot
# ---------------------------

bot.run(TOKEN)
