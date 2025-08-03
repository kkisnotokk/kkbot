from discord.ext import commands
@commands.command(help="Rick, clip that")
async def threesixtynoscope(ctx):
    await ctx.send("https://tenor.com/view/360noscope-gif-18161400")

def setup(bot):
    bot.add_command(threesixtynoscope)