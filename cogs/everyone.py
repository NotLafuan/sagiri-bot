import discord
from discord.ext import commands
import time
from utils import send_notice, MESSAGE, SILVER


class everyone(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(help='<text to repeat>', description='Make Sagiri say something.\n`[Everyone]`')
    async def say(self, ctx: commands.Context, *, query: str):
        await ctx.message.delete()
        await ctx.send(query)

    @commands.group(name='ping', aliases=['latency', 'lat'], invoke_without_command=True, help='', description='Shows the latency of the bot.\n`[Everyone]`')
    async def ping(self, ctx: commands.Context):
        await send_notice(ctx, f'Pong! `{round(self.client.latency * 1000)}ms`', notice_type=MESSAGE)

    @ping.command(name='ws', aliases=['websocket'], help='', description='Shows the websocket latency of the bot.\n`[Everyone]`')
    async def ping_ws(self, ctx: commands.Context):
        start_time = time.perf_counter()
        message = await send_notice(ctx, f'Pong!', notice_type=MESSAGE)
        ping = (time.perf_counter() - start_time) * 1000
        embed = discord.Embed(
            description=f'Pong! `{int(ping)}ms`',
            color=SILVER
        )
        await message.edit(embed=embed)


def setup(client: commands.Bot):
    client.add_cog(everyone(client))
