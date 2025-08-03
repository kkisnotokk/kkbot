# main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import importlib

# Load .env token
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="<",
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none(),
    help_command=commands.DefaultHelpCommand()
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

TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
