from discord.ext import commands
@commands.command(help="IS THAT A SURVIV REFERENCE??")
async def reviv(ctx):
    await ctx.send("Not only did you make a typo, but you also used the wrong prefix, AND you also referenced Surviv.")
    
def setup(bot):
    bot.add_command(reviv)