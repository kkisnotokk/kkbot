from discord.ext import commands
from discord.utils import escape_markdown, escape_mentions
from main import rigged_responses
import random
@commands.command(help="Rates anything from 1/10 to 100/10")
async def rate(ctx, *, thing: str): # if thing is empty its automatically translated to False
    rigged = rigged_responses.pop(ctx.author.id, None)
    if rigged:
        await ctx.send(f"🎯 {rigged} *(rigged)*")
        return

    if not thing:
        await ctx.send("📊 Rate what? Example: `<rate Blundy's habit of reacting in the shadows.`")
        return

    score = random.choice(
        list(range(1, 11)) + [69, 100, 0, -1, 404, 456]  # Spice it up
    )
    
    await ctx.send(f"📊 I'd rate **{escape_mentions(escape_markdown(thing))}** a solid **{score}/10**")
    
def setup(bot):
    bot.add_command(rate)