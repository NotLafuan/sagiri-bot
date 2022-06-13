import discord
from discord.ext import commands
import time
from utils import *

DEVELOPER_ID = 319485284465115147


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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content == self.client.user.mention:
            prefix = get_prefix(self.client, message)
            developer = await self.client.fetch_user(DEVELOPER_ID)

            title = 'Server settings information'
            text = f'''Server prefix: `{prefix}`
            Server ID: `{message.guild.id}`

            Join a voice channel and `{prefix}play` a song.
            Type `{prefix}help` for the list of commands.'''
            # [Invite]({INVITE_LINK})

            embed = discord.Embed(title=title, description=text, color=SILVER)
            embed.set_footer(text=f'Developed by {developer}')
            await message.channel.send(embed=embed)
        await self.client.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        ignored = (commands.NoPrivateMessage, commands.DisabledCommand, commands.CheckFailure,
                   commands.CommandNotFound, discord.HTTPException, commands.NotOwner)
        error = getattr(error, 'original', error)
        if isinstance(error, ignored):
            pass
        elif isinstance(error, commands.MissingPermissions):
            text = str(error)
            # You are missing Manage Messages and Manage Nicknames permission(s) to run this command.
            text = text.replace('(s)', '')
            text = text[:-32] + '`' + text[-32:]
            text = text[:16] + '`' + text[16:]
            text = text.replace(' and ', '` and `')
            # You are missing `Manage Messages` and `Manage Nicknames` permission to run this command.
            await send_notice(ctx, text, notice_type=WARNING)
        elif isinstance(error, commands.MissingRequiredArgument):
            text = f'Some argument(s) are not provided.\nHave a look at `{get_prefix(self.client, ctx.message)}help {ctx.command.name}`'
            await send_notice(ctx, text)
        elif isinstance(error, commands.UserInputError):
            text = f'Invalid argument provided.\nHave a look at `{get_prefix(self.client, ctx.message)}help {ctx.command.name}`'
            await send_notice(ctx, text)
        else:
            print(error.__class__.__name__, ' > ', error)


def setup(client: commands.Bot):
    client.add_cog(everyone(client))
