import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from discord.utils import escape_mentions, escape_markdown
import random
import re
import asyncio
sniped_messages = {}

load_dotenv()  # loads .env file

TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True  # Required to read user messages

bot = commands.Bot(command_prefix="<", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}!")


@bot.command()
async def roll(ctx, *, args):
    async def replace_mentions(text):
        mention_pattern = r'<@!?(\d+)>'

        async def replace(match):
            user_id = int(match.group(1))
            # Try to get member from guild cache
            member = ctx.guild.get_member(user_id) if ctx.guild else None
            if member:
                return f"@{member.display_name}"
            try:
                user = await bot.fetch_user(user_id)
                return f"@{user.name}"
            except discord.NotFound:
                return "@unknown"

        # Use asyncio-compatible replacement for re.sub
        parts = []
        last_end = 0
        for match in re.finditer(mention_pattern, text):
            parts.append(text[last_end:match.start()])
            parts.append(await replace(match))
            last_end = match.end()
        parts.append(text[last_end:])
        return ''.join(parts)

    # Replace mentions in args
    cleaned_args = await replace_mentions(args)

    # Handle roll logic
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





@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    if message.content.startswith('<echo'):
        # Delete the user's message
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException as e:
            print(f"Failed to delete message: {e}")

        # Extract text after <echo
        text_to_echo = message.content[len('<echo'):].strip()

        if text_to_echo:
            await message.channel.send(text_to_echo)

    # Process other commands if you have any
    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def revive(ctx):
    await ctx.send("Sorry but I won't steal the jobs of my fellow bots, unless it's RNGesus, screw that guy.")

@bot.command()
async def mango(ctx):
    await ctx.send("🍋")
    
@bot.command()
async def lemon(ctx):
    await ctx.send("🥭")

@bot.command()
async def gamble(ctx):
    import random

    # Slot options
    symbols = ["🥭", "🍋", "🥝", "0️⃣", "💀", "⭐", "7️⃣"]

    # Spin 3 reels
    result = [random.choice(symbols) for _ in range(3)]
    slot_display = " | ".join(result)

    # Logic for result
    if result.count(result[0]) == 3:
        response = f"🎉 JACKPOT! {slot_display} - You win big!"
    elif len(set(result)) == 2:
        response = f"So close! {slot_display} - You almost had it."
    else:
        response = f"{slot_display} - Better luck next time."

    await ctx.send(response)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return  # ignore deleted bot messages

    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }
@bot.command()
async def snipe(ctx):
    snipe_data = sniped_messages.get(ctx.channel.id)

    if snipe_data:
        time_diff = (discord.utils.utcnow() - snipe_data["time"]).seconds
        await ctx.send(
            f"Deleted message by **{snipe_data['author']}** ({time_diff} seconds ago):\n> {snipe_data['content']}"
        )
    else:
        await ctx.send("There's nothing to snipe, stop being paranoid lmao")


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


bot.run(TOKEN)
