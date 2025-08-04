# other_commands/rig.py

import discord
from discord.ext import commands

# This will be overwritten by main.py's version after import
rigged_responses = {}

class Rig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Rig the bot's next <roll, <eightball, or <rate response to say what you want.")
    async def rig(self, ctx, *, message: str):
        rigged_responses[ctx.author.id] = message
        await ctx.send(f":3 Your next command is rigged to say: `{message}`")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.author.id in rigged_responses:
            rigged_msg = rigged_responses.pop(ctx.author.id)
            await ctx.send(f"[RIGGED] {rigged_msg}")
            raise commands.CheckFailure("RIGGED: command execution halted.")

def setup(bot):
    # Assign the shared dictionary to the cog’s copy
    from main import rigged_responses as shared_rigged
    globals()["rigged_responses"] = shared_rigged

    bot.add_cog(Rig(bot))
