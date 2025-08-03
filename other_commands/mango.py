from discord.ext import commands
@commands.command(help="yvlis")
async def mango(ctx):
    await ctx.send("🍋")

def setup(bot):
    bot.add_command(mango)