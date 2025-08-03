from discord.ext import commands
@commands.command(help="Greets the user")
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}!")
    
def setup(bot):
    bot.add_command(hello)