import discord
from discord.ext import commands
from utils import *

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEVELOPER_ID = 319485284465115147

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
async def on_message(message: discord.Message):
    if message.content == client.user.mention:
        prefix = get_prefix(client, message)
        developer = await client.fetch_user(DEVELOPER_ID)

        title = 'Server settings information'
        text = f'''Server prefix: `{prefix}`
        Server ID: `{message.guild.id}`

        Join a voice channel and `{prefix}play` a song.
        Type `{prefix}help` for the list of commands.'''
        # [Invite]({INVITE_LINK})

        embed = discord.Embed(title=title, description=text, color=SILVER)
        embed.set_footer(text=f'Developed by {developer}')
        await message.channel.send(embed=embed)
    await client.process_commands(message)


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
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
        text = f'Some argument(s) are not provided.\nHave a look at `{get_prefix(client, ctx.message)}help {ctx.command.name}`'
        await send_notice(ctx, text)
    elif isinstance(error, commands.UserInputError):
        text = f'Invalid argument provided.\nHave a look at `{get_prefix(client, ctx.message)}help {ctx.command.name}`'
        await send_notice(ctx, text)
    else:
        print(error.__class__.__name__, ' > ', error)


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


@client.command()
@commands.is_owner()
async def reloadall(ctx: commands.Context):
    print(f'\n #################### Reload All #################### \n')
    for cog in cogs:
        if cog != 'database':
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
                    embed = discord.Embed(
                        description=error, color=discord.Color.red())
                    await ctx.send(embed=embed)
            except Exception as e:
                error = str(e).replace('\'', '`')
                embed = discord.Embed(
                    description=error, color=discord.Color.red())
                await ctx.send(embed=embed)

client.run(BOT_TOKEN)
