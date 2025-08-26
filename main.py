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

# --- Tierlist system (persistent, default emoji mapping, private/public) ---
import json
import os

TIERLISTS_FILE = "tierlists.json"

def load_tierlists():
    if os.path.exists(TIERLISTS_FILE):
        with open(TIERLISTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tierlists(data):
    with open(TIERLISTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Structure:
# tierlists = {
#   "<id>": {
#       "owner": "<user_id_as_str>",
#       "private": True|False,
#       "is_default": True|False,
#       "tiers": { "s": [...], "a": [...], ... }  # or custom names
#   }
# }

tierlists = load_tierlists()

# Emoji display map for default lists
DEFAULT_DISPLAY_MAP = {
    "s": "🇸 🔴",
    "a": "🇦 🟠",
    "b": "🇧 🟠",
    "c": "🇨 🟡",
    "d": "🇩 🟢",
    "e": "🇪 🟢",
    "f": "🇫 🔵",
}
# Reverse map to resolve emoji tokens to keys (e.g. '🇸' -> 's', '🔴' -> 's')
EMOJI_TO_KEY = {}
for k, v in DEFAULT_DISPLAY_MAP.items():
    for token in v.split():
        EMOJI_TO_KEY[token] = k

def format_tierlist(tid, tl):
    """Return a string representation of a tierlist (with emoji labels for default)."""
    lines = [f"--Tierlist (ID: {tid})--"]
    if tl.get("is_default"):
        # maintain order s,a,b,c,d,e,f
        for key in ["s","a","b","c","d","e","f"]:
            if key in tl["tiers"]:
                items = tl["tiers"][key]
                label = DEFAULT_DISPLAY_MAP.get(key, key.upper())
                lines.append(f"{label}: {', '.join(items) if items else '(empty)'}")
    else:
        # custom tier order follows insertion order of dict
        for tier_name, items in tl["tiers"].items():
            lines.append(f"{tier_name}: {', '.join(items) if items else '(empty)'}")
    return "\n".join(lines)

def normalize_tierlist_id(tid):
    return str(tid)

def resolve_tier_key(tl, raw_tier_input):
    """
    Given a tierlist object and user-supplied tier string, return the
    internal tier key (exact key used in tl['tiers']) or None.
    For default lists, accepts 's' or 'S' or '🇸' or '🔴' or '🇸 🔴'.
    For custom lists, accepts case-insensitive exact matches to tier names.
    """
    if raw_tier_input is None:
        return None
    t = raw_tier_input.strip()
    if not t:
        return None

    # if default list: internal keys are single-letter lowercases
    if tl.get("is_default"):
        s = t.lower()
        # direct single-letter match
        if len(s) == 1 and s in tl["tiers"]:
            return s
        # first-letter (in case user typed "S-tier" etc.)
        first = s[0]
        if first in tl["tiers"]:
            return first
        # check for emoji tokens inside the input
        for ch in t:
            if ch in EMOJI_TO_KEY:
                return EMOJI_TO_KEY[ch]
        # maybe input is the full label "🇸 🔴"
        normalized = " ".join(t.split())
        for k, lab in DEFAULT_DISPLAY_MAP.items():
            if normalized == lab:
                return k
        return None
    else:
        # custom tiers: match case-insensitive to tier name keys
        s = t.lower()
        for key in tl["tiers"].keys():
            if s == key.lower():
                return key
        return None

PRESETS_FILE = "presets.json"

# --- Built-in presets ---
builtin_presets = {
    "rplyr": [f"player {str(i).zfill(2)}" for i in range(1, 41)],  # player 01 - player 40
    "rma": [
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
    ]
}

# --- Load custom presets ---
def load_presets():
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_presets(presets):
    with open(PRESETS_FILE, "w") as f:
        json.dump(presets, f, indent=2)

custom_presets = load_presets()
# Merge built-in & custom for places that expect `roll_presets`
roll_presets = {**builtin_presets, **custom_presets}

# ---------------------------
# EVENTS
# ---------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle <echo manually
    try:
        if message.content.startswith('<echo'):
            await message.delete()
            text_to_echo = message.content[len('<echo'):].strip()
            if text_to_echo:
                await message.channel.send(text_to_echo)
                return
    except Exception as e:
        print(f"[on_message error] {e}")

    # Handle roll preset shortcut (<presetname)
    if message.content.startswith("<"):
        cmd_name = message.content[1:].lower()  # strip '<' and lowercase
        if cmd_name in roll_presets:
            choice = random.choice(roll_presets[cmd_name])
            await message.channel.send(f"🎲 {message.author.mention}, your roll from `{cmd_name}` is: **{choice}**")
            return

    # Let normal commands work
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
        time_diff = int((discord.utils.utcnow() - snipe_data["time"]).total_seconds())
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
    fake_ping = "@" + "\u200b".join(fake_ping)   # zero-width join to prevent real ping
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

# --- Command to create presets ---
@bot.command(name="create_roll_preset")
async def create_roll_preset(ctx, name: str, *, content: str):
    options = [opt.strip() for opt in content.split(",")]
    custom_presets[name] = options
    save_presets(custom_presets)

    # keep the merged view in sync
    global roll_presets
    roll_presets = {**builtin_presets, **custom_presets}

    await ctx.send(f"Preset **{name}** created with {len(options)} options!")

# --- Command to use rpreset ---
@bot.command(name="rpreset")
async def rpreset(ctx, *, template: str):
    output = template

    # Merge built-ins and custom presets
    all_presets = {**builtin_presets, **custom_presets}

    # Replace placeholders
    for preset_name, preset_values in all_presets.items():
        placeholder = f"({preset_name})"
        while placeholder in output:
            choice = random.choice(preset_values)
            output = output.replace(placeholder, choice, 1)

    await ctx.send(output)

# ---- Command to list presets ----
@bot.command(name="list_roll_presets")
async def list_roll_presets(ctx):
    if not roll_presets:
        await ctx.send("📭 No roll presets saved yet.")
        return
    preset_list = ", ".join(roll_presets.keys())
    await ctx.send(f"🎲 Available roll presets: {preset_list}")

# ---- Custom command handler for <preset_name ----
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)

    # Check if user typed a preset command
    if message.content.startswith("<"):
        cmd_name = message.content[1:].lower()  # strip '<' and lowercase
        if cmd_name in roll_presets:
            import random
            choice = random.choice(roll_presets[cmd_name])
            await message.channel.send(f"🎲 {message.author.mention}, your roll from `{cmd_name}` is: **{choice}**")
            return

    await bot.process_commands(message)

# --- Built-in presets ---
builtin_presets = {
    "rplyr": [f"player {str(i).zfill(2)}" for i in range(1, 41)],  # player 01 - player 40
    "rma": [
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
    ]
}

@bot.command(name="create", help="Create a tierlist: <create tierlist (id) (private? yes/no) (default|comma,separated,tiernames)>")
async def create_tierlist(ctx, arg, tierlist_id: str, private_flag: str, *, tiers: str):
    # expects: <create tierlist 1 yes default>  OR <create tierlist 2 no A-tier,B-tier>
    if arg.lower() != "tierlist":
        await ctx.send("Usage: `<create tierlist (id) (private? yes/no) (default|tier1,tier2,...)`")
        return

    tid = normalize_tierlist_id(tierlist_id)
    if tid in tierlists:
        await ctx.send(f"A tierlist with ID `{tid}` already exists.")
        return

    priv = private_flag.lower() in ("yes", "y", "true", "1")
    is_def = tiers.lower().strip() == "default"

    if is_def:
        keys = ["s","a","b","c","d","e","f"]
        tiers_dict = {k: [] for k in keys}
    else:
        # custom names (keep original casing as keys)
        names = [t.strip() for t in tiers.split(",") if t.strip()]
        if not names:
            await ctx.send("You must supply at least one tier name, or use 'default'.")
            return
        tiers_dict = {name: [] for name in names}

    tierlists[tid] = {
        "owner": str(ctx.author.id),
        "private": bool(priv),
        "is_default": bool(is_def),
        "tiers": tiers_dict
    }
    save_tierlists(tierlists)
    await ctx.send(format_tierlist(tid, tierlists[tid]))

@bot.command(name="rank", help="Rank an item in a tierlist: <rank (id) (item) (tier)> — tier can be letter/emoji for default lists")
async def rank_item(ctx, tierlist_id: str, item: str, *, tier: str):
    tid = normalize_tierlist_id(tierlist_id)
    if tid not in tierlists:
        await ctx.send("That tierlist ID does not exist.")
        return

    tl = tierlists[tid]
    # permissions: if private, only owner can edit; if public, anyone can edit
    if tl.get("private") and str(ctx.author.id) != str(tl.get("owner")):
        await ctx.send("This tierlist is private — only the creator can edit it.")
        return

    key = resolve_tier_key(tl, tier)
    if key is None:
        await ctx.send("Could not resolve that tier name/emoji. Check the tier list with `<viewtierlist`.")
        return

    # remove item from any tier (case-insensitive match)
    for k, items in tl["tiers"].items():
        tl["tiers"][k] = [x for x in items if x.lower() != item.lower()]

    # append to new tier (use internal key for default lists; for custom lists key can be full name)
    tl["tiers"][key].append(item)
    save_tierlists(tierlists)
    await ctx.send(format_tierlist(tid, tl))

@bot.command(name="removeitem", help="Remove an item from a tierlist: <removeitem (id) (item)>")
async def remove_item(ctx, tierlist_id: str, *, item: str):
    tid = normalize_tierlist_id(tierlist_id)
    if tid not in tierlists:
        await ctx.send("That tierlist ID does not exist.")
        return
    tl = tierlists[tid]
    if tl.get("private") and str(ctx.author.id) != str(tl.get("owner")):
        await ctx.send("This tierlist is private — only the creator can edit it.")
        return

    removed = False
    for k, items in tl["tiers"].items():
        new_items = [x for x in items if x.lower() != item.lower()]
        if len(new_items) != len(items):
            removed = True
        tl["tiers"][k] = new_items

    if removed:
        save_tierlists(tierlists)
        await ctx.send(format_tierlist(tid, tl))
    else:
        await ctx.send(f"'{item}' was not found in tierlist {tid}.")

@bot.command(name="deletetierlist", help="Delete a tierlist: <deletetierlist (id)> (creator only)")
async def delete_tierlist(ctx, tierlist_id: str):
    tid = normalize_tierlist_id(tierlist_id)
    if tid not in tierlists:
        await ctx.send("That tierlist ID does not exist.")
        return
    if str(ctx.author.id) != str(tierlists[tid]["owner"]):
        await ctx.send("Only the creator can delete this tierlist.")
        return
    del tierlists[tid]
    save_tierlists(tierlists)
    await ctx.send(f"Tierlist `{tid}` has been deleted.")

@bot.command(name="viewtierlist", help="View a tierlist: <viewtierlist (id)>")
async def view_tierlist(ctx, tierlist_id: str):
    tid = normalize_tierlist_id(tierlist_id)
    if tid not in tierlists:
        await ctx.send("That tierlist ID does not exist.")
        return
    await ctx.send(format_tierlist(tid, tierlists[tid]))

    
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
