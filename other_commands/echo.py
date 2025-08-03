from discord.ext import commands
from discord.utils import escape_mentions, escape_markdown
@commands.command(name="echo") # idk why did you put it in on_message
async def echo(ctx, *, message: str):
    await ctx.message.delete()
    clean_message = escape_mentions(escape_markdown(message))
    await ctx.send(clean_message)

def setup(bot):
    bot.add_command(echo)