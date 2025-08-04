import discord
from discord.ext import commands

rigged_responses = {}

class Rig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rigged_responses = rigged_responses

    @commands.command(help="Rig the bot's next response to a command.")
    async def rig(self, ctx, *, message: str):
        self.rigged_responses[ctx.author.id] = message
        await ctx.send(f":3 Your next command is rigged to say: `{message}`")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.author.id in self.rigged_responses:
            rigged_msg = self.rigged_responses.pop(ctx.author.id)
            await ctx.send(f"[RIGGED] {rigged_msg}")
            raise commands.CheckFailure("RIGGED: command execution halted.")

def setup(bot):
    bot.add_cog(Rig(bot))
