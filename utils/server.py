import discord
from discord.ext import commands
from dataclasses import dataclass
from itertools import cycle
import json
from typing import Mapping, Optional

ERROR = 'error'
WARNING = 'warning'
MESSAGE = 'message'

SILVER: discord.Color = discord.Color.from_rgb(r=203, g=213, b=225)

EMPTY_CHAR = '‎'


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], list[commands.Command]]):
        embed = discord.Embed(color=SILVER)
        embed.set_author(
            name='Help Command',
            icon_url=self.context.bot.user.avatar_url
        )
        for cog, _commands in mapping.items():
            if cog and cog.qualified_name != 'database':
                name = f'{cog.qualified_name} commands'.capitalize()
                value = ', '.join(
                    [f'`{command.name}`' for command in _commands]
                )
                embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(
            text=f'Type \'{self.clean_prefix}help <CommandName>\' for details on a command'
        )
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        name = f'{cog.qualified_name} commands'.capitalize()
        value = ', '.join(
            [f'`{command.name}`' for command in cog.get_commands()]
        )

        embed = discord.Embed(color=SILVER)
        embed.set_author(
            name='Category',
            icon_url=self.context.bot.user.avatar_url
        )
        embed.add_field(name=name, value=value, inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(
            color=SILVER,
            description='Aliases: ' +
            ', '.join([f'`{alias}`' for alias in group.aliases]
                      ) if group.aliases else discord.Embed.Empty
        )
        embed.set_author(
            name=f'Help Command: {group.name}',
            icon_url=self.context.bot.user.avatar_url
        )
        arguments = group.help.split('|')
        descriptions = group.description.split('|')
        for argument, description in zip(arguments, descriptions):
            embed.add_field(
                name=f'{self.clean_prefix}{group.name} {argument}',
                value=f'{description}\n{EMPTY_CHAR}',
                inline=False
            )

        _commands: list[commands.Command] = list(group.commands)
        for command in _commands:
            arguments = command.help.split('|')
            descriptions = command.description.split('|')
            if command != _commands[-1]:
                for argument, description in zip(arguments, descriptions):
                    embed.add_field(
                        name=f'{self.clean_prefix}{group.name} {command.name} {argument}',
                        value=f'{description}\n{EMPTY_CHAR}',
                        inline=False
                    )
            else:
                for argument, description in zip(arguments, descriptions):
                    embed.add_field(
                        name=f'{self.clean_prefix}{group.name} {command.name} {argument}',
                        value=f'{description}',
                        inline=False
                    )
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            color=SILVER,
            description='Aliases: ' +
            ', '.join([f'`{alias}`' for alias in command.aliases]
                      ) if command.aliases else discord.Embed.Empty
        )
        embed.set_author(
            name=f'Help Command: {command.name}',
            icon_url=self.context.bot.user.avatar_url
        )
        arguments = command.help.split('|')
        descriptions = command.description.split('|')
        for argument, description in zip(arguments, descriptions):
            if argument != arguments[-1]:
                embed.add_field(
                    name=f'{self.clean_prefix}{command.name} {argument}',
                    value=f'{description}\n{EMPTY_CHAR}',
                    inline=False
                )
            else:
                embed.add_field(
                    name=f'{self.clean_prefix}{command.name} {argument}',
                    value=f'{description}',
                    inline=False
                )
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str):
        error = error.replace('"', '`')
        embed = discord.Embed(description=error, color=discord.Color.red())
        msg: discord.Message = await self.get_destination().send(embed=embed)
        await msg.delete(delay=3)


def get_prefix(client: commands.Bot, message: discord.Message):
    return client.server_info[message.guild.id].prefix


@dataclass
class ServerInfo():
    """Store all the server specific information.

    Attributes
    -----------
    prefix: :class:`str`
        The server's prefix.
    volume: :class:`float`
        The music's volume level.
    loop: :class:`str`
        The current loop mode.
    """
    prefix: str
    volume: float
    loop: str
    loop_modes = cycle(['queue', 'song', 'disabled'])

    def cycle_loop(self):
        self.loop = next(self.loop_modes)


def load_info(client: commands.Bot, filename: str = 'server_info.json'):
    with open(filename, 'r') as f:
        server_info = json.load(f)

    for guild in client.guilds:
        if str(guild.id) in server_info:
            properties = server_info[str(guild.id)]
            client.server_info[guild.id] = ServerInfo(**properties)
        else:
            client.server_info[guild.id] = ServerInfo('.', 100., 'off')

    save_info(client)


def save_info(client: commands.Bot, filename: str = 'server_info.json'):
    save_dict: dict = {}

    for guild in client.server_info:
        save_dict[guild] = {
            'prefix': client.server_info[guild].prefix,
            'volume': client.server_info[guild].volume,
            'loop': client.server_info[guild].loop,
        }

    with open(filename, 'w+') as f:
        json.dump(save_dict, f, indent=4, ensure_ascii=False)


def add_info(client: commands.Bot, guild: discord.Guild):
    client.server_info[guild.id] = ServerInfo('.', 100., 'off')


def remove_info(client: commands.Bot, guild: discord.Guild):
    client.server_info.pop(guild.id)


async def send_notice(messageable: discord.abc.Messageable, message: str, notice_type: str = ERROR, delay: int | None = None) -> discord.Message:
    if notice_type == ERROR:
        color = discord.Color.red()
    elif notice_type == WARNING:
        color = discord.Color.gold()
    elif notice_type == MESSAGE:
        color = SILVER
    embed = discord.Embed(
        description=message,
        color=color
    )
    notice: discord.Message = await messageable.send(embed=embed)
    if delay:
        await notice.delete(delay=delay)
    return notice
