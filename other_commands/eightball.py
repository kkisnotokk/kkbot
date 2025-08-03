from discord.ext import commands
from discord.utils import escape_mentions, escape_markdown
from main import rigged_responses
import random

@commands.command(help="Ask the all-knowing 8-ball a question")
async def eightball(ctx, *, question: str): # if question is empty its automatically translated to False
    rigged = rigged_responses.pop(ctx.author.id, None)
    if rigged:
        await ctx.send(f"❌ {rigged}")
        return
    
    responses = [
        "Yes.", "No.", "Maybe.", "Absolutely.", "Absolutely not.",
        "Ask again later.", "OUT OF ALL THE QUESTIONS YOU CAN ASK, YOU ASK THAT?",
        "Without a doubt.", "I wouldn’t count on it.",
        "I'm tired of your dumb questions, go ask Emilybot.", "Try again after touching grass.", "You really don't want me to answer that",
        "Idk ask Emilybot.", "All will be clear soon, wait, no it won't I lied you're cooked.",
        f"It's ggs {ctx.author.name}, you know the answer.", "Er uh you don't need to know that.",
        "I am not answering that.", "Shut up I'm busy getting drunk.",
        "@kk there's been an error, I think I ran out of shits to give."
    ]

    if not question:
        await ctx.send("🎱 You need to ask a question. Example: `<8ball will i get pinged`")
        return

    answer = random.choice(responses)
    clean_answer = escape_mentions(escape_markdown(answer))
    await ctx.send(f"🎱 {clean_answer}")

def setup(bot):
    bot.add_command(eightball)