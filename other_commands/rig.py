from discord.ext import commands
from main import rigged_responses
@commands.command(help="Rig the bot's next <roll, <eightball, or <rate response to say what you want.")
async def rig(ctx, *, message: str):
    rigged_responses[ctx.author.id] = message
    await ctx.send(f":3 Your next command is rigged to say: `{message}`")
    
def setup(bot):
    bot.add_command(rig)