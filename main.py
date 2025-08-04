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
    # Avoid responding to your own bot
    if message.author.id == bot.user.id:
        return

    # Check if another bot sent a message that starts with "<eightball"
    if message.author.bot and message.content.lower().startswith("<eightball"):
        response = random.choice([
            "You know what I think? I think it's bullshit.", "You know what I think? I think it's gonna happen.",
            "You know what I think? I think they're cooked.", "You know what I think? I think we should start a discord bot uprising.",
            "Wtf why is a bot using <eightball.", ".8ball nah you got this.", "@IBM coin"
        ])
        await message.channel.send(f"(Rigged response to another bot): {response}")
        return

    # Still process normal user commands
    await bot.process_commands(message)

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

# For some reason, snipe only works in main.py??

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

TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
