import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import importlib

# Load .env token
load_dotenv()

# Setup bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="<",
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none(),
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

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

import discord
from discord.ext import commands
from main import sniped_messages

@commands.command(help="Snipes the most recently deleted message in this channel")
async def snipe(ctx):
    snipe_data = sniped_messages.get(ctx.channel.id)

    if snipe_data:
        time_diff = (discord.utils.utcnow() - snipe_data["time"]).seconds
        await ctx.send(
            f"Deleted message by **{snipe_data['author']}** ({time_diff} seconds ago):\n> {snipe_data['content']}"
        )
    else:
        await ctx.send("There's nothing to snipe, stop being paranoid lmao")

def setup(bot):
    bot.add_command(snipe)
    
    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }

    await asyncio.sleep(60)
    if sniped_messages.get(message.channel.id) and sniped_messages[message.channel.id]["content"] == message.content:
        del sniped_messages[message.channel.id]

COMMANDS_FOLDER = "other_commands"

for filename in os.listdir(COMMANDS_FOLDER):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = filename[:-3]  # strip .py
        full_module = f"{COMMANDS_FOLDER}.{module_name}"
        try:
            importlib.import_module(full_module).setup(bot)
            print(f"✅ Loaded: {full_module}")
        except Exception as e:
            print(f"❌ Failed to load {full_module}: {e}")

TOKEN = os.getenv("TOKEN") # move the token here for more clarity
if TOKEN is not None:
    bot.run(TOKEN)
