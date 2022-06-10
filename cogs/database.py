import discord
from discord.ext import commands
from utils import ServerMusic
from typing import Dict

SILVER: discord.Color = discord.Color.from_rgb(r=203, g=213, b=225)


class database(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.ready: bool = False
        self.server_music: Dict[int, ServerMusic] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.client.server_info:
            self.server_music[guild] = ServerMusic()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.server_music[guild.id] = ServerMusic()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.server_music.pop(guild.id)


def setup(client: commands.Bot):
    client.add_cog(database(client))
