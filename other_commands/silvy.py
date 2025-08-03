from discord.ext import commands
@commands.command(help="silvy")
async def lemon(ctx):
    await ctx.send("🥭")
    
def setup(bot):
    bot.add_command(lemon)