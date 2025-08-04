# main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import importlib

# Load .env token
load_dotenv()

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(
    command_prefix="<",
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none()
)

# Shared data structures
sniped_messages = {}
rigged_responses = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # SNIPING support
    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }
    # Schedule cleanup
    async def delete_sniped():
        await asyncio.sleep(60)
        if sniped_messages.get(message.channel.id) and sniped_messages[message.channel.id]["content"] == message.content:
            del sniped_messages[message.channel.id]
    asyncio.create_task(delete_sniped())

    # RIGGING support
    ctx = await bot.get_context(message)
    if ctx.valid and message.author.id in rigged_responses:
        response = rigged_responses.pop(message.author.id)
        await message.channel.send(response)
        return  # Skip original command

    # Normal processing
    await bot.process_commands(message)

# Load all commands in subfolder
COMMANDS_FOLDER = "other_commands"

for filename in os.listdir(COMMANDS_FOLDER):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = filename[:-3]
        full_module = f"{COMMANDS_FOLDER}.{module_name}"
        try:
            importlib.import_module(full_module).setup(bot)
            print(f"✅ Loaded: {full_module}")
        except Exception as e:
            print(f"❌ Failed to load {full_module}: {e}")

# For some reason, snipe & rig only works in main.py??

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

# CHATGPT BUGFIX BELOW

@bot.command(name="rig")
async def rig(ctx, *, message: str):
    rigged_responses[ctx.author.id] = message
    await ctx.send(f"✅ Your next response has been rigged to: `{message}`")

    # Only hijack if it's a valid command AND the user is rigged
    if ctx.valid and message.author.id in rigged_responses:
        response = rigged_responses.pop(message.author.id)
        await message.channel.send(response)
        return  # Skip original command

    # No rigging? Process normally
    await bot.process_commands(message)
    
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
