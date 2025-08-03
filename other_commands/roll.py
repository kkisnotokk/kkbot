import discord
from discord.ext import commands
import random
import re
from main import rigged_responses

async def replace_mentions(ctx: commands.Context, text: str) -> str:
    async def mention_replacer(match):
        user_id = int(match.group(1))
        member = ctx.guild.get_member(user_id) if ctx.guild else None
        if member:
            return f"@{member.display_name}"
        try:
            user = await ctx.bot.fetch_user(user_id)
            return f"@{user.name}"
        except discord.NotFound:
            return "@unknown"

    # Replace all mentions asynchronously
    parts = []
    pos = 0
    for match in re.finditer(r'<@!?(\d+)>', text):
        parts.append(text[pos:match.start()])
        parts.append(await mention_replacer(match))
        pos = match.end()
    parts.append(text[pos:])
    return ''.join(parts)

@commands.command(help="Choose between words or roll a number (e.g. <roll 10 or <roll red, blue)")
async def roll(ctx: commands.Context, *, args: str):
    if (rigged := rigged_responses.pop(ctx.author.id, None)):
        return await ctx.send(f"🎯 {rigged} *(rigged)*")

    cleaned = await replace_mentions(ctx, args)
    
    if ',' in cleaned:
        choices = [c.strip() for c in cleaned.split(',') if c.strip()]
        if len(choices) < 2:
            return await ctx.send("❌ Please provide at least two comma-separated choices.")
        return await ctx.send(f"🎲 You rolled: {random.choice(choices)}")
    
    try:
        upper = int(cleaned.strip().split()[0])
        if upper <= 0:
            raise ValueError
        return await ctx.send(f"🎲 You rolled: {random.randint(1, upper)}")
    except (ValueError, IndexError):
        return await ctx.send(
            "❌ Usage:\n- `<roll 100` → random number from 1–100\n- `<roll red, blue, green` → pick from choices"
        )

def setup(bot):
    bot.add_command(roll)