import discord
from discord.ext import commands
from utils import *
from datetime import datetime, timedelta
from cogs.database import database


class admin(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.database: database = self.client.get_cog('database')

    async def connect(self, ctx: commands.Context) -> bool:
        server_music = self.database.server_music[ctx.guild.id]
        if server_music.vc:
            await server_music.vc.move_to(ctx.author.voice.channel)
            return True
        if ctx.author.voice:
            server_music.vc = await ctx.author.voice.channel.connect()
            return True
        await send_notice(ctx, 'You\'re not in a voice channel.')
        return False

    @commands.command(help='|<new prefix>', description='Show the current prefix.\n`[Everyone]`|Lets you set a new prefix.\n`[Manage Server]`')
    async def sagiriprefix(self, ctx: commands.Context, prefix: str | None):
        server_info: dict[int, ServerInfo] = self.client.server_info
        if not prefix:
            prefix = server_info[ctx.guild.id].prefix
            await send_notice(ctx, f'Server prefix is `{prefix}`', notice_type=MESSAGE)
            return
        permissions = ctx.author.permissions_in(ctx.channel)
        if not permissions.manage_guild:
            await send_notice(ctx, 'You are missing `Manage Server` permission to run this command.', notice_type=WARNING)
            return
        server_info[ctx.guild.id].prefix = prefix
        await send_notice(ctx, f'Prefix changed to `{prefix}`', notice_type=WARNING)
        save_info(self.client)

    def check(self, message: discord.Message):
        prefix = self.client.command_prefix(self.client, message)
        commands_aliases = [command.name for command in self.client.commands]
        commands_aliases += [
            alias for command in self.client.commands for alias in command.aliases]
        if message.author == self.client.user:
            return True
        elif message.content == self.client.user.mention:
            return True
        elif message.content.startswith(prefix):
            if message.content.split()[0][len(prefix):] in commands_aliases:
                return True
        return False

    @commands.group(aliases=['cleanup'], invoke_without_command=True, help='', description='Clear command and bot messages.\n`[Manage Messages]`')
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx: commands.Context):
        await ctx.message.delete()
        deleted = await ctx.channel.purge(check=self.check, after=datetime.utcnow()-timedelta(days=14), oldest_first=False)
        await send_notice(ctx, f'Cleaning up `{len(deleted)}` messages.', notice_type=MESSAGE, delay=10)

    @clean.command(name='all', help='<amount>', description='Clear all messages for pass 14 days.\n`[Manage Messages]`')
    @commands.has_permissions(manage_messages=True)
    async def clean_all(self, ctx: commands.Context, limit: int = 100):
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow()-timedelta(days=14), oldest_first=False)
        await send_notice(ctx, f'Cleaning up `{len(deleted)}` messages.', notice_type=MESSAGE, delay=10)

    @clean.command(name='purge', help='<amount>', description='Clear all messages.\n*Slower than **clean all***\n`[Manage Messages]`')
    @commands.has_permissions(manage_messages=True)
    async def clean_purge(self, ctx: commands.Context, limit: int = 100):
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit, oldest_first=False)
        await send_notice(ctx, f'Cleaning up `{len(deleted)}` messages.', notice_type=MESSAGE, delay=10)

    @commands.command(aliases=['summon', 'connect'], help='', description='Makes the bot join your voice channel.\n`[Admin]`')
    @commands.has_permissions(administrator=True)
    async def join(self, ctx: commands.Context):
        if await self.connect(ctx):
            await ctx.message.add_reaction('✅')

    @commands.command(aliases=['dc', 'disconnect'], help='', description='Disconnects the bot from its current voice channel.\n`[Admin]`')
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: commands.Context):
        server_music = self.database.server_music[ctx.guild.id]
        if not server_music.vc:
            await send_notice(ctx, 'The bot is currently not in a voice channel.', notice_type=ERROR)
            return
        await server_music.vc.disconnect()
        server_music.vc = None
        await ctx.message.add_reaction('✅')


async def setup(client: commands.Bot):
    await client.add_cog(admin(client))
