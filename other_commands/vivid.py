from discord.ext import commands
@commands.command(help="it's vivid")
async def vivid(ctx):
    await ctx.send("Holy shit is it time for another vividstory? I better make sure my kids don't see this.")

def setup(bot):
    bot.add_command(vivid)