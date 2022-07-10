from utils import *
from typing import Dict


class database(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.ready: bool = False
        self.server_music: Dict[int, ServerMusic] = {}
        for guild in self.client.server_info:
            self.server_music[guild] = ServerMusic()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.server_music[guild.id] = ServerMusic()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.server_music.pop(guild.id)


async def setup(client: commands.Bot):
    await client.add_cog(database(client))
