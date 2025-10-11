import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
# from discord.utils import escape_mentions, escape_markdown  # unused; keep or remove
import random
import re
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta

# ==== POLL SYSTEM ====

POLL_FILE = "polls.json"

# Load/save persistent poll data
def load_polls():
    if not os.path.exists(POLL_FILE):
        return {}
    with open(POLL_FILE, "r") as f:
        return json.load(f)

def save_polls(polls):
    with open(POLL_FILE, "w") as f:
        json.dump(polls, f, indent=4)

polls = load_polls()

# Helper: create embed view of poll
def make_poll_embed(poll_name, data, closed=False):
    embed = discord.Embed(
        title=f"🗳️ Poll — {poll_name}",
        description=data["question"],
        color=discord.Color.blurple()
    )
    for option, stats in data["options"].items():
        first = len([v for v in data["votes"].values() if v[0] == option])
        second = len([v for v in data["votes"].values() if len(v) > 1 and v[1] == option])
        third = len([v for v in data["votes"].values() if len(v) > 2 and v[2] == option])
        embed.add_field(
            name=f"{option}",
            value=f"🥇 **{first}** 🥈 {second} 🥉 {third}",
            inline=False
        )
    if not closed:
        end_time = datetime.fromisoformat(data["end_time"])
        embed.set_footer(text=f"Poll ends at {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        embed.color = discord.Color.green()
    return embed

# Instant-runoff vote counting
def compute_irv_winner(votes, options):
    remaining = set(options)
    while True:
        counts = {opt: 0 for opt in remaining}
        for vote in votes.values():
            for choice in vote:
                if choice in remaining:
                    counts[choice] += 1
                    break
        # Check if any candidate has >50%
        total = sum(counts.values())
        for opt, c in counts.items():
            if c > total / 2:
                return opt, counts
        # Eliminate lowest
        min_votes = min(counts.values())
        losers = [o for o, c in counts.items() if c == min_votes]
        for l in losers:
            remaining.remove(l)
        if len(remaining) == 1:
            return next(iter(remaining)), counts


ECON_FILE = "economy.json"

# ---------------- Economy Helper Functions ---------------- #
def load_econ():
    if not os.path.exists(ECON_FILE):
        return {"users": {}}
    with open(ECON_FILE, "r") as f:
        return json.load(f)

def save_econ(data):
    with open(ECON_FILE, "w") as f:
        json.dump(data, f, indent=4)

econ_data = load_econ()

def get_user_data(user_id):
    if str(user_id) not in econ_data["users"]:
        econ_data["users"][str(user_id)] = {
            "shares": 0,
            "opted_in": False,
            "first_time": True,
            "last_opt_time": 0
        }
    return econ_data["users"][str(user_id)]


TIERLISTS_FILE = "tierlists.json"

# Load tierlists from file
def load_tierlists():
    if os.path.exists(TIERLISTS_FILE):
        with open(TIERLISTS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save tierlists to file
def save_tierlists(data):
    with open(TIERLISTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

tierlists = load_tierlists()

def format_tierlist(tierlist_id, tierlist):
    output = f"--Tierlist (ID: {tierlist_id})--\n"
    for tier, items in tierlist["tiers"].items():
        if items:
            output += f"{tier}: {', '.join(items)}\n"
        else:
            output += f"{tier}: (empty)\n"
    return output

# Presets are now server-specific
# Structure: { guild_id: { preset_name: [values...] } }
server_presets = {}

# Built-in presets (always available across all servers)
built_in_presets = {
    "rplyr": [
        "king blunderer",
        "apollix",
        "Kuyicon",
        "Emily",
        "silvy",
        "no one",
        "Pezut",
        "Chezmosis",
        "Py Rick",
        "M",
        "TampliteSK",
        "Almostgood",
        "Anti",
        "Chicken Nugget",
        "Ral",
        "darth vader",
        "erixero",
        "Beniu1305",
        "Ghoda",
        "jsaidoru",
        "Surviv_34",
        "Mrsir_real",
        "Kan",
        "!kk!",
        "ManosSef",
        "myloRAHH",
        "NotBaltic",
        "sted",
        "SudokuFan",
        "vivid",
        "Sealandball",
        "ⁱᶜᵉ³"
    ],
    "rma": ["player 01", "player 02", "player 03", "player 04", "player 05",
            "player 06", "player 07", "player 08", "player 09", "player 10",
            "player 11", "player 12", "player 13", "player 14", "player 15",
            "player 16", "player 17", "player 18", "player 19", "player 20",
            "player 21", "player 22", "player 23", "player 24", "player 25",
            "player 26", "player 27", "player 28", "player 29", "player 30",
            "player 31", "player 32", "player 33", "player 34", "player 35",
            "player 36", "player 37", "player 38", "player 39", "player 40"]
}

REMINDERS_FILE = "reminders.json"

if os.path.exists(REMINDERS_FILE):
    with open(REMINDERS_FILE, "r") as f:
        reminders = json.load(f)
else:
    reminders = []

def save_reminders():
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f)

async def reminder_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = time.time()
        due = [r for r in reminders if r["time"] <= now]
        for r in due:
            try:
                channel = bot.get_channel(r["channel"])
                if channel:
                    user = f"<@{r['user']}>"
                    task = f" Reminder: {r['task']}" if r["task"] else ""
                    await channel.send(f"WEWOWEWO {user}{task}")
            except Exception as e:
                print(f"Error sending reminder: {e}")
            reminders.remove(r)
            save_reminders()
        await asyncio.sleep(5)

# Load .env token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Setup bot
intents = discord.Intents.default()
intents.message_content = True  # needed for on_message and content parsing

bot = commands.Bot(
    command_prefix="<",
    intents=intents,
    help_command=commands.DefaultHelpCommand(),
)

sniped_messages = {}
rigged_responses = {}
STARTING_TIME = 12 * 60 * 60  # 12 hours
chess_games = {}
edited_messages = {}       
deleted_message_logs = {}  

# ---------------------------
# EVENTS
# ---------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")
    bot.loop.create_task(reminder_loop())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

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



@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    edited_messages[before.channel.id] = {
        "before": before.content,
        "after": after.content,
        "author": before.author,
        "time": before.edited_at
    }

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }

    if message.channel.id not in deleted_message_logs:
        deleted_message_logs[message.channel.id] = []
    deleted_message_logs[message.channel.id].append({
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    })

    await asyncio.sleep(60)
    if sniped_messages.get(message.channel.id) and sniped_messages[message.channel.id]["content"] == message.content:
        del sniped_messages[message.channel.id]

    if message.channel.id in deleted_message_logs:
        deleted_message_logs[message.channel.id] = [
            msg for msg in deleted_message_logs[message.channel.id] if msg["content"] != message.content
        ]
        if not deleted_message_logs[message.channel.id]:
            del deleted_message_logs[message.channel.id]

async def poll_autoclose():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.utcnow()
        for name, data in list(polls.items()):
            if not data.get("closed", False) and datetime.fromisoformat(data["end_time"]) <= now:
                data["closed"] = True
                winner, final_counts = compute_irv_winner(data["votes"], data["options"].keys())
                save_polls(polls)

                channel = bot.get_channel(data["channel"])
                if channel:
                    result_embed = discord.Embed(
                        title=f"✅ Poll Results — {name}",
                        description=f"🏆 **{winner}** wins!\nQuestion: {data['question']}",
                        color=discord.Color.green()
                    )
                    for opt, count in final_counts.items():
                        result_embed.add_field(name=opt, value=f"Final Votes: **{count}**", inline=False)
                    await channel.send(embed=result_embed)
        await asyncio.sleep(60)  # check every minute

bot.loop.create_task(poll_autoclose())

# ---------------------------
# COMMANDS
# ---------------------------

@bot.command(help="Greets the user")
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}, kinda weird talking to a bot but you do you")

@bot.command(help="Checks if the bot is running")
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command(name="echo")
async def echo(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

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
    await ctx.send("\u200b")  # zero-width space so it's a valid message

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

    await ctx.send(response + f"/n {ctx.author.name} used <gamble")

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
            await ctx.send(f"🎲 You rolled: {result}" + "\n" + f"-# {ctx.author.name} used <roll")
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
            await ctx.send(f"🎲 You rolled: {result}" + "\n" + f"-# {ctx.author.name} used <roll")
            return
        except ValueError:
            pass

    await ctx.send("❌ Usage:\n- <roll 100 → random number from 1–100\n- <roll red, blue, green → pick from choices")

@bot.command(help="Snipes the most recently deleted message in this channel")
async def snipe(ctx):
    snipe_data = sniped_messages.get(ctx.channel.id)

    if snipe_data:
        time_diff = int((discord.utils.utcnow() - snipe_data["time"]).total_seconds())
        await ctx.send(
            f"# Deleted message by **{snipe_data['author']}** ({time_diff} seconds ago):\n---\n>>> {snipe_data['content']}"
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
    fake_ping = "@" + "\u200b".join(fake_ping)   # zero-width join to prevent real ping
    await ctx.send(fake_ping)

@bot.command(name="eightball" , aliases=["8ball"] , help="Ask the all-knowing 8-ball a question")
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
        "@kk there's been an error, I think I ran out of shits to give.", "(Sponsored) We are sorry to interupt this command but we must inform you of the hot new bot on the market— @IBM!! You should use '@IBM coin' and try it now!!",
        "You should be careful useing 8ball nowadays, the 8ball throwing man has started visiting other bots" , "LOOK OUT IT'S A FLYING 8BALL"
    ]

    if not question:
        await ctx.send("🎱 You need to ask a question. Example: <8ball will i get pinged")
        return

    answer = random.choice(responses)
    await ctx.send(f"🎱 {answer}" + "\n" + f"-# {ctx.author.name} used <eightball")

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
async def dictionary(ctx, *, word: str):
    """
    Looks up the definition of a word using Free Dictionary API.
    Usage: <dictionary example
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

@bot.command(name="summarize", help="Condense the replied-to message into its core meaning")
async def summarize(ctx):
    if not ctx.message.reference:
        await ctx.send("↩️ Please reply to the message you want summarized.")
        return

    replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    text = replied_message.content.strip()

    if not text:
        await ctx.send("❌ That message has no text to summarize.")
        return

    words = text.split()
    if len(words) <= 12:
        condensed = text
    else:
        condensed = " ".join(words[:8] + ["..."] + words[-4:])

    await ctx.send(condensed)

@bot.command(name="remind", aliases=["reminder"], help="Set a reminder: <remind 10m close this suggestion>")
async def remind(ctx, time_input: str, *, task: str = ""):
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        unit = time_input[-1]
        if unit not in units:
            await ctx.send("❌ Invalid time format. Use s/m/h/d (e.g., 10m, 2h).")
            return
        amount = int(time_input[:-1])
        if amount <= 0:
            await ctx.send("❌ Time must be greater than 0.")
            return
        delay = amount * units[unit]
    except ValueError:
        await ctx.send("❌ Invalid time. Example: `<remind 10m Do homework>`")
        return

    remind_time = int(time.time() + delay)
    reminders.append({
        "user": ctx.author.id,
        "channel": ctx.channel.id,
        "time": remind_time,
        "task": task
    })
    save_reminders()

    await ctx.send(
        f"Okk, I’ll remind you {f'to {task}' if task else ''} "
        f"<t:{remind_time}:R> (**<t:{remind_time}:F>**)."
    )

@bot.command(name="reminders", help="View your pending reminders")
async def reminders_cmd(ctx):
    user_reminders = [r for r in reminders if r["user"] == ctx.author.id]

    if not user_reminders:
        await ctx.send(" You don’t have any pending reminders.")
        return

    lines = []
    for i, r in enumerate(sorted(user_reminders, key=lambda x: x["time"]), 1):
        task_text = f" → {r['task']}" if r["task"] else ""
        lines.append(
            f"**{i}.** <t:{int(r['time'])}:R> (**<t:{int(r['time'])}:F>**){task_text}"
        )

    await ctx.send(
        f" **Your reminders:**\n" + "\n".join(lines)
    )

@bot.command(name="cancelreminder", aliases=["cancelreminders", "delreminder", "deletereminder"], help="Cancel one of your reminders by its number (see <reminders>)")
async def cancel_reminder(ctx, number: int):
    user_reminders = [r for r in reminders if r["user"] == ctx.author.id]

    if not user_reminders:
        await ctx.send("You don’t have any reminders to cancel.")
        return

    if number < 1 or number > len(user_reminders):
        await ctx.send(f"Invalid reminder number. Use `<reminders` to see valid numbers.")
        return

    reminder_to_cancel = sorted(user_reminders, key=lambda x: x["time"])[number - 1]
    reminders.remove(reminder_to_cancel)

    save_reminders()

    task_text = f" → {reminder_to_cancel['task']}" if reminder_to_cancel["task"] else ""
    await ctx.send(
        f"Reminder #{number} has been cancelled: <t:{int(reminder_to_cancel['time'])}:F>{task_text}"
    )

@bot.command(name="addpreset", help="Create a pool of options that kkbot can roll from. Usage: <addpreset {preset name} {poll of options seperated by commas}")
async def addpreset(ctx, name: str, *, values: str):
    """Add a new server-specific preset."""
    guild_id = ctx.guild.id
    if guild_id not in server_presets:
        server_presets[guild_id] = {}

    values_list = [v.strip() for v in values.split(",")]
    server_presets[guild_id][name] = values_list
    await ctx.send(f"Preset `{name}` added for this server with {len(values_list)} values." + f"\n -# {ctx.author.name} used <addpreset")

@bot.command(name="deletepreset", help="Delete a preset. Usage: <deletepreset (preset name}")
async def deletepreset(ctx, name: str):
    """Delete a preset in this server."""
    guild_id = ctx.guild.id
    if guild_id not in server_presets or name not in server_presets[guild_id]:
        await ctx.send(f"Preset `{name}` does not exist in this server.")
        return

    del server_presets[guild_id][name]
    await ctx.send(f"Preset `{name}` deleted from this server.")

@bot.command(name="list_roll_presets", help="list all presets in your server")
async def list_roll_presets(ctx):
    """List available presets (server + built-in)."""
    guild_id = ctx.guild.id
    server_list = list(server_presets.get(guild_id, {}).keys())
    builtin_list = list(built_in_presets.keys())

    msg = "**Available presets:**\n"
    if server_list:
        msg += f"Server-specific: {', '.join(server_list)}\n"
    else:
        msg += "Server-specific: (none)\n"

    msg += f"Built-in: {', '.join(builtin_list)}"
    await ctx.send(msg)

@bot.command(name="rpreset", help="Replace (preset_name) with random values from that preset.")
async def rpreset(ctx, *, text: str):
    """Replace (preset_name) with random values from that preset."""
    guild_id = ctx.guild.id

    def replace_preset(match):
        preset_name = match.group(1)
        # Check server-specific presets first
        if guild_id in server_presets and preset_name in server_presets[guild_id]:
            return random.choice(server_presets[guild_id][preset_name])
        # Then check built-ins
        elif preset_name in built_in_presets:
            return random.choice(built_in_presets[preset_name])
        else:
            return f"(preset `{preset_name}` doesn't exist)"

    import re
    pattern = re.compile(r"\((.*?)\)")
    result = pattern.sub(replace_preset, text)

    await ctx.send(result)

@bot.command(name="create", help="Create a tierlist: <create tierlist (id) (comma-separated tiers or 'default')>")
async def create_tierlist(ctx, arg, tierlist_id: str, *, tiers: str):
    if arg.lower() != "tierlist":
        return

    if tierlist_id in tierlists:
        await ctx.send(f"A tierlist with ID `{tierlist_id}` already exists!")
        return

    if tiers.lower() == "default":
        tier_names = ["S", "A", "B", "C", "D", "E", "F"]
    else:
        tier_names = [t.strip() for t in tiers.split(",")]

    tierlists[tierlist_id] = {
        "owner": str(ctx.author.id),
        "tiers": {t: [] for t in tier_names}
    }

    save_tierlists(tierlists)
    await ctx.send(format_tierlist(tierlist_id, tierlists[tierlist_id]))

@bot.command(name="rank", help="Rank an item in a tierlist: <rank (id) (item) (tier)>")
async def rank_item(ctx, tierlist_id: str, item: str, *, tier: str):
    if tierlist_id not in tierlists:
        await ctx.send("That tierlist does not exist.")
        return
    if str(ctx.author.id) != tierlists[tierlist_id]["owner"]:
        await ctx.send("Only the creator of this tierlist can edit it.")
        return
    if tier not in tierlists[tierlist_id]["tiers"]:
        await ctx.send("That tier does not exist in this tierlist.")
        return

    # Remove from all tiers first
    for t in tierlists[tierlist_id]["tiers"].values():
        if item in t:
            t.remove(item)

    # Add to new tier
    tierlists[tierlist_id]["tiers"][tier].append(item)
    save_tierlists(tierlists)
    await ctx.send(format_tierlist(tierlist_id, tierlists[tierlist_id]))

@bot.command(name="removeitem", help="Remove an item from a tierlist: <removeitem (id) (item)>")
async def remove_item(ctx, tierlist_id: str, *, item: str):
    if tierlist_id not in tierlists:
        await ctx.send("That tierlist does not exist.")
        return
    if str(ctx.author.id) != tierlists[tierlist_id]["owner"]:
        await ctx.send("Only the creator of this tierlist can edit it.")
        return

    for t in tierlists[tierlist_id]["tiers"].values():
        if item in t:
            t.remove(item)

    save_tierlists(tierlists)
    await ctx.send(format_tierlist(tierlist_id, tierlists[tierlist_id]))

@bot.command(name="deletetierlist", help="Delete a tierlist: <deletetierlist (id)>")
async def delete_tierlist(ctx, tierlist_id: str):
    if tierlist_id not in tierlists:
        await ctx.send("That tierlist does not exist.")
        return
    if str(ctx.author.id) != tierlists[tierlist_id]["owner"]:
        await ctx.send("Only the creator of this tierlist can delete it.")
        return

    del tierlists[tierlist_id]
    save_tierlists(tierlists)
    await ctx.send(f"Tierlist `{tierlist_id}` deleted.")

@bot.command(name="viewtierlist", help="View a tierlist: <viewtierlist (id)>")
async def view_tierlist(ctx, tierlist_id: str):
    if tierlist_id not in tierlists:
        await ctx.send("That tierlist does not exist.")
        return
    await ctx.send(format_tierlist(tierlist_id, tierlists[tierlist_id]))

@bot.command(help="Start a chess timer game. Usage: <startgame [game_id]")
async def startgame(ctx, game_id: str):
    if game_id in chess_games:
        await ctx.send(f"NEIN game `{game_id}` already exists.")
        return

    chess_games[game_id] = {
        "white": {"time": STARTING_TIME, "running": True},
        "black": {"time": STARTING_TIME, "running": False},
        "last_update": time.time(),
        "creator": ctx.author.id,
    }

    await ctx.send(f"Game `{game_id}` started! White's clock (12h) is now running.")

@bot.command(help="End your turn and switch clocks. Usage: <endturn [game_id]")
async def endturn(ctx, game_id: str):
    if game_id not in chess_games:
        await ctx.send(f"Gang what are we on- game `{game_id}` does not exist.")
        return

    game = chess_games[game_id]
    now = time.time()
    elapsed = now - game["last_update"]

    if game["white"]["running"]:
        game["white"]["time"] -= elapsed
        game["white"]["running"] = False
        game["black"]["running"] = True
        side = "Black ⚫"
    else:
        game["black"]["time"] -= elapsed
        game["black"]["running"] = False
        game["white"]["running"] = True
        side = "White ⚪"

    game["last_update"] = now
    await ctx.send(f"Turn ended- {side}'s clock is now running")

@bot.command(help="View the currently running side’s remaining time. Usage: <viewtime [game_id]")
async def viewtime(ctx, game_id: str):
    if game_id not in chess_games:
        await ctx.send(f"Did you make a typo or smth??? Game `{game_id}` does not exist")
        return

    game = chess_games[game_id]
    now = time.time()
    elapsed = now - game["last_update"]

    if game["white"]["running"]:
        remaining = game["white"]["time"] - elapsed
        side = "White ⚪"
    else:
        remaining = game["black"]["time"] - elapsed
        side = "Black ⚫"

    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    seconds = int(remaining % 60)

    await ctx.send(f"{side} has **{hours}h {minutes}m {seconds}s** left in game `{game_id}`.")

@bot.command(help="End the game and show both sides’ remaining times. Usage: <endgame [game_id]")
async def endgame(ctx, game_id: str):
    if game_id not in chess_games:
        await ctx.send(f"Are we serious rn game `{game_id}` does not exist.")
        return

    game = chess_games.pop(game_id)
    now = time.time()
    elapsed = now - game["last_update"]

    if game["white"]["running"]:
        game["white"]["time"] -= elapsed
    else:
        game["black"]["time"] -= elapsed

    def fmt_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h}h {m}m {s}s"

    await ctx.send(
        f"Norway game `{game_id}` ended (I hope Rail won)\n"
        f"⚪ White: {fmt_time(game['white']['time'])}\n"
        f"⚫ Black: {fmt_time(game['black']['time'])}"
    )

# ---------------- Economy Commands ---------------- #
@bot.command(help="Opt in/out of the shares economy. Usage: <shares opt in / opt out")
async def shares(ctx, action: str = None, action2: str = None):
    global econ_data
    user_id = str(ctx.author.id)
    user_data = get_user_data(user_id)

    if action == "opt" and action2 == "in":
        now = time.time()
        # Enforce 1 week cooldown (7 days = 604800 seconds)
        if not user_data["opted_in"]:
            if now - user_data["last_opt_time"] < 604800 and not user_data["first_time"]:
                remaining = 604800 - (now - user_data["last_opt_time"])
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                minutes = int((remaining % 3600) // 60)
                return await ctx.send(f"⏳ You can opt in again in {days}d {hours}h {minutes}m.")

            user_data["opted_in"] = True
            user_data["last_opt_time"] = now

            if user_data["first_time"]:
                user_data["shares"] = 100
                user_data["first_time"] = False
                await ctx.send(f"✅ {ctx.author.mention} opted in and received **100 shares**!")
            else:
                await ctx.send(f"✅ {ctx.author.mention} opted back in with **{user_data['shares']} shares**.")

        else:
            await ctx.send("⚠️ You are already opted in.")

    elif action == "opt" and action2 == "out":
        if user_data["opted_in"]:
            user_data["opted_in"] = False
            user_data["shares"] = 0
            user_data["last_opt_time"] = time.time()
            await ctx.send(f"{ctx.author.mention} opted out. Your shares have been set to **0**.")
        else:
            await ctx.send("⚠️ You are not opted in.")

    else:
        await ctx.send("⚠️ Usage: `<shares opt in>` or `<shares opt out>`")

    save_econ(econ_data)


@bot.command(help="View the shares leaderboard. Usage: <leaderboard")
async def leaderboard(ctx):
    global econ_data
    users = econ_data["users"]
    # Only include users with >0 shares
    leaderboard_list = [(int(uid), data["shares"]) for uid, data in users.items() if data["shares"] > 0]

    if not leaderboard_list:
        return await ctx.send("Nobody has shares yet.")

    leaderboard_list.sort(key=lambda x: x[1], reverse=True)
    lines = []
    for i, (uid, shares) in enumerate(leaderboard_list[:10], start=1):  # Top 10
        user = await bot.fetch_user(uid)
        lines.append(f"**{i}. {user.name}** — {shares} shares")

    await ctx.send("🏆 **Shares Leaderboard** 🏆\n" + "\n".join(lines))


@bot.command(help="⚠️ (Owner only) Reset the entire economy. Usage: <resetecon")
@commands.is_owner()
async def resetecon(ctx):
    global econ_data
    econ_data = {"users": {}}
    save_econ(econ_data)
    await ctx.send("⚠️ Economy has been completely reset.")


# uhhh back to normalcy

@bot.command(help="Snipes the last edited message in this channel")
async def editsnipe(ctx):
    data = edited_messages.get(ctx.channel.id)
    if data:
        await ctx.send(
            f"A message was edited by... \n"
            f"# **{data['author']}**\n"
            f" # <:d_:1409192999136792766><:d_:1409192999136792766><:d_:1409192999136792766> \n"
            f"-# ◄══════════════════════►\n"
            f"***Before:*** {data['before']}\n"
            f"-# ◄══════════════════════►\n"
            f"***After:*** {data['after']}\n"
            f"-# {ctx.author.name} used <editsnipe"
        )
    else:
        await ctx.send("No message was edited in the last minute, so you're either late or paranoid.")


@bot.command(help="Snipes all deleted messages from the past 60 seconds in this channel")
async def snipeall(ctx):
    logs = deleted_message_logs.get(ctx.channel.id, [])
    if not logs:
        return await ctx.send("Nope, nothing **AND I MEAN NOTHING** was deleted in the last minute <:d_:1409192999136792766>")

    lines = []
    for msg in logs:
        time_diff = (discord.utils.utcnow() - msg["time"]).seconds
        lines.append(f"**{msg['author']}** ({time_diff}s ago): {msg['content']}")

    await ctx.send(
        f"# GET SNIPED <:KEKW:1363718257835769916>:\n"
        f"Here are **ALL** deleted messages in the past minute \n" + "\n".join(lines[:10]) + "\n" + f"-# {ctx.author.name} used <snipeall")

# Poll stuff:

@bot.command(help="Create a new ranked-choice poll")
async def createpoll(ctx, *, args):
    try:
        name, question, options_str, duration = [a.strip() for a in args.split("|")]
        duration = int(duration)
    except Exception:
        await ctx.send("Usage: `<createpoll name | question | option1, option2, option3 | duration(min)>`")
        return

    if name in polls:
        await ctx.send("A poll with that name already exists <:KEKW:1363718257835769916>")
        return

    options = [o.strip() for o in options_str.split(",")]
    polls[name] = {
        "creator": ctx.author.id,
        "question": question,
        "options": {opt: {} for opt in options},
        "votes": {},
        "end_time": (datetime.utcnow() + timedelta(minutes=duration)).isoformat(),
        "channel": ctx.channel.id,
        "message_id": None,
        "closed": False
    }

    embed = make_poll_embed(name, polls[name])
    msg = await ctx.send(embed=embed)
    polls[name]["message_id"] = msg.id
    save_polls(polls)
    await ctx.send(f"Poll **{name}** created! Use `<vote {name} opt1, opt2, opt3>` to vote.")

@bot.command(help="Vote in a ranked-choice poll")
async def vote(ctx, poll_name, *, ranked_choices):
    if poll_name not in polls:
        await ctx.send("404 poll not found")
        return

    poll = polls[poll_name]
    if poll["closed"]:
        await ctx.send("You're a little late bro this poll is closed.")
        return

    options = [o.strip().lower() for o in poll["options"].keys()]
    votes = [v.strip().lower() for v in ranked_choices.split(",")]

    if not all(v in options for v in votes):
        await ctx.send("Invalid option(s) in your vote (CHECK YOUR SPELLING)")
        return

    poll["votes"][str(ctx.author.id)] = votes
    save_polls(polls)
    await ctx.send(f"Vote recorded for poll **{poll_name}**!")

    # Update the live poll message
    try:
        channel = bot.get_channel(poll["channel"])
        msg = await channel.fetch_message(poll["message_id"])
        await msg.edit(embed=make_poll_embed(poll_name, poll))
    except Exception:
        pass

@bot.command(help="End a poll early (poll creator only)")
async def endpoll(ctx, poll_name):
    if poll_name not in polls:
        await ctx.send("404 poll not found.")
        return
    poll = polls[poll_name]
    if ctx.author.id != poll["creator"]:
        await ctx.send("Only the poll creator can end the poll.")
        return
    if poll["closed"]:
        await ctx.send("Poll already closed <:KEKW:1363718257835769916>")
        return

    poll["closed"] = True
    winner, final_counts = compute_irv_winner(poll["votes"], poll["options"].keys())
    save_polls(polls)

    result_embed = discord.Embed(
        title=f"Poll Results — {poll_name}",
        description=f"Option **{winner}** has for **{poll['question']}**",
        color=discord.Color.green()
    )
    for opt, count in final_counts.items():
        result_embed.add_field(name=opt, value=f"Final Votes: **{count}**", inline=False)

    await ctx.send(embed=result_embed)

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
        await interaction.response.defer()  # acknowledge the interaction
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("boardrepresentation")
        await ctx.invoke(command)

class EvaluationButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Done reading? You may want to know about evaluating too", style=discord.ButtonStyle.success)
    async def go_to_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("evaluation")
        await ctx.invoke(command)

class MinimaxButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="You might want to read about Minimax too", style=discord.ButtonStyle.success)
    async def go_to_minimax(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("minimax")
        await ctx.invoke(command)

class AlphaBetaButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="You might also want to optimize Minimax", style=discord.ButtonStyle.success)
    async def go_to_alphabeta(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("alphabeta")
        await ctx.invoke(command)

class MoveOrderingButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Optimize Alpha-Beta pruning", style=discord.ButtonStyle.success)
    async def go_to_moveordering(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("moveordering")
        await ctx.invoke(command)

class TranspositionTableButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Save even more searching time?", style=discord.ButtonStyle.success)
    async def go_to_transpositiontable(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message)
        ctx.interaction = interaction
        command = self.bot.get_command("transpositiontable")
        await ctx.invoke(command)

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
    invert_color=True,  # Invert the color of the black pieces
    borders=False,      # Shows borders around the board
    empty_square=".",   # The character for empty squares
    orientation=chess.WHITE  # The orientation of the board
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
