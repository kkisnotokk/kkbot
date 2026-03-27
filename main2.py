import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import os
import random
import re
import asyncio

def format_ts(dt: datetime, style: str = "F") -> str:
    ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
    return f"<t:{ts}:{style}>"

LOG_CHANNEL_ID = 1482774398435065949
FORUMS_CHANNEL_ID = 1482757775833563237

class InviteLogger(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}
        
    async def cog_load(self):
        await self.update_invite_cache()
        
    async def update_invite_cache(self):
        for guild in self.bot.guilds:
            try: self.cache[guild.id] = await guild.invites()
            except discord.Forbidden: pass

    @commands.Cog.listener()
    async def on_member_join(self,  member: discord.Member):
        guild = member.guild
        ch = self.bot.get_channel(LOG_CHANNEL_ID)
        before = self.cache.get(guild.id) or []
        try:
            after = await guild.invites()
            self.cache[guild.id] = after


            used = None
            for inv_after in after:
                orig = discord.utils.get(before, code=inv_after.code)
                if orig is None and inv_after.uses and inv_after.uses >= 1:
                    used = inv_after
                    break
                if orig and inv_after.uses > orig.uses:
                    used = inv_after
                    break

            embed = discord.Embed(color=0x2ECC71, timestamp=datetime.now(timezone.utc))
            embed.set_author(name="🟢 Member Joined", icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)

            embed.add_field(name="Name", value=str(member), inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Created", value=format_ts(member.created_at, "F"), inline=False)
            embed.add_field(name="Account Created", value=format_ts(member.created_at, "R"), inline=False)
            embed.add_field(name="Joined Server", value=format_ts(member.joined_at or datetime.now(timezone.utc), "F"), inline=False)

            if used:
                inv = used
                invite_fields = {
                    "Invite Code": inv.code,
                    "Inviter": inv.inviter.mention if inv.inviter else "Unknown",
                    "Channel": ("#" + inv.channel.name) if inv.channel else "Unknown",
                    "Uses": inv.uses or "Unknown",
                    "Max Uses": inv.max_uses or "Unlimited",
                    "Expires": format_ts(inv.expires_at, "F") if getattr(inv, "expires_at", None) else "Never",
                    "Temporary": str(inv.temporary)
                }
                for n, v in invite_fields.items():
                    embed.add_field(name=n, value=v, inline=True)

                # embed.add_field(name="Invite URL", value=inv.url, inline=False)
            else:
                embed.add_field(name="Invite", value="Failed to fetch invite!", inline=False)

            await ch.send(embed=embed)
        except discord.Forbidden as e:
            ch.send(e.with_traceback())

    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(color=0xE74C3C, timestamp=datetime.now(timezone.utc))
        embed.set_author(name="🔴 Member Left", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="Name", value=str(member), inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)

        await ch.send(embed=embed)

    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        ch = self.bot.get_channel(LOG_CHANNEL_ID)
        if not ch:
            return
        
        embed = discord.Embed(color=0x00ADEF, timestamp=datetime.now(timezone.utc))
        embed.set_author(name="📨 New Invite Created", icon_url=invite.inviter.display_avatar.url)
        embed.add_field(name="Created By", value=invite.inviter.mention if invite.inviter else "Unknown", inline=True)
        embed.add_field(name="Code", value=f"`{invite.code}`", inline=True)
        embed.add_field(name="Channel", value=invite.channel.name if invite.channel else "Unknown", inline=True)

        max_uses = invite.max_uses or "Unlimited"
        embed.add_field(name="Max Uses", value=str(max_uses), inline=True)

        if invite.expires_at:
            embed.add_field(name="Expires In", value=format_ts(invite.expires_at, "R"), inline=True)
        else:
            embed.add_field(name="Expires In", value="Never", inline=True)

        embed.add_field(name="Temporary Membership", value=str(invite.temporary), inline=True)

        embed.add_field(name="Invite URL", value=invite.url, inline=False)

        await ch.send(embed=embed)

        # Update invites_cache so no invite slips in between.
        await self.update_invite_cache()


async def setup(bot: commands.Bot):
    await bot.add_cog(InviteLogger(bot))
