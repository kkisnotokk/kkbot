from discord.ext import commands
@commands.command(help="It's kk")
async def kk(ctx):
    await ctx.send("...is not okk")

def setup(bot):
    bot.add_command(kk)