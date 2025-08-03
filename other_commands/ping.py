from discord.ext import commands
@commands.command(help="Checks if the bot is running")
async def ping(ctx):
    await ctx.send("Pong!")
    
def setup(bot):
    bot.add_command(ping)