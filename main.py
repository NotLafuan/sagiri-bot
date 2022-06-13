import discord
from discord.ext import commands
from utils import *

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
    load_info(client)


@client.event
async def on_guild_join(guild: discord.Guild):
    add_info(client, guild)
    save_info(client)


@client.event
async def on_guild_remove(guild: discord.Guild):
    remove_info(client, guild)
    save_info(client)


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
