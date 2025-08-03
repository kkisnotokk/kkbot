from discord.ext import commands
@commands.command(help="pew pew")
async def sniper(ctx):
    await ctx.send("Yes hello I'm here what do you need?")

def setup(bot):
    bot.add_command(sniper)