from discord.ext import commands
@commands.command(help="Mocks your sentence. Example: `<mock I am serious`")
async def mock(ctx, *, text: str):  # if text is empty its automatically translated to False
    if not text:
        await ctx.send("What do you want me to mock? Example: `<mock you always say that`")
        return

    mocked = ''.join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )
    await ctx.send(f"{mocked}")
    
def setup(bot):
    bot.add_command(mock)