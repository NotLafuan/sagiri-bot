import discord
from discord.ext import commands
from utils import WARNING, CustomHelpCommand, load_info, save_info, add_info, remove_info, get_prefix, send_notice

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv('BOT_TOKEN')

client = commands.Bot(
    command_prefix=get_prefix,
    help_command=CustomHelpCommand(),
    case_insensitive=True
)

client.server_info = {}

cogs = ['database', 'everyone', 'music', 'admin', 'extra']
for cog in cogs:
    client.load_extension(f'cogs.{cog}')


@client.event
async def on_ready():
    print(f'{client.user} is ready.')
    client.mention = f'<@!{client.user.id}>'
    load_info(client)


@client.event
async def on_guild_join(guild: discord.Guild):
    add_info(client, guild)
    save_info(client)


@client.event
async def on_guild_remove(guild: discord.Guild):
    remove_info(client, guild)
    save_info(client)


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    ignored = (commands.NoPrivateMessage, commands.DisabledCommand, commands.CheckFailure,
               commands.CommandNotFound, commands.UserInputError, discord.HTTPException,
               commands.NotOwner)
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
        text = f'Some argument(s) are not provided.\nHave a look at `{get_prefix(client, ctx.message)}help {ctx.command.name}`'
        await send_notice(ctx, text)
    else:
        text = f'Invalid argument provided.\nHave a look at `{get_prefix(client, ctx.message)}help {ctx.command.name}`'
        await send_notice(ctx, text)


@client.command()
@commands.is_owner()
async def load(ctx: commands.Context, cog: str):
    print(f'\n #################### Load {cog} #################### \n')
    try:
        client.load_extension(f'cogs.{cog}')
        await ctx.message.add_reaction('✅')
    except Exception as e:
        error = str(e).replace('\'', '`')
        embed = discord.Embed(description=error, color=discord.Color.red())
        await ctx.send(embed=embed)


@client.command()
@commands.is_owner()
async def unload(ctx: commands.Context, cog: str):
    print(f'\n #################### Unload {cog} #################### \n')
    try:
        client.unload_extension(f'cogs.{cog}')
        await ctx.message.add_reaction('✅')
    except Exception as e:
        error = str(e).replace('\'', '`')
        embed = discord.Embed(description=error, color=discord.Color.red())
        await ctx.send(embed=embed)


@client.command()
@commands.is_owner()
async def reload(ctx: commands.Context, cog: str):
    print(f'\n #################### Reload {cog} #################### \n')
    try:
        client.unload_extension(f'cogs.{cog}')
        client.load_extension(f'cogs.{cog}')
        await ctx.message.add_reaction('✅')
    except commands.ExtensionNotLoaded:
        try:
            client.load_extension(f'cogs.{cog}')
            await ctx.message.add_reaction('✅')
        except Exception as e:
            error = str(e).replace('\'', '`')
            embed = discord.Embed(description=error, color=discord.Color.red())
            await ctx.send(embed=embed)
    except Exception as e:
        error = str(e).replace('\'', '`')
        embed = discord.Embed(description=error, color=discord.Color.red())
        await ctx.send(embed=embed)

client.run(BOT_TOKEN)
