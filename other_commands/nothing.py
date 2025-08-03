from discord.ext import commands
@commands.command(help="nothing")
async def nothing(ctx):
    await ctx.send("")
    
def setup(bot):
    bot.add_command(nothing)