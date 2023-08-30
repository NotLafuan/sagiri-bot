from utils import *
import numpy as np

import spacy
nlp = spacy.load('en_core_web_sm')


def accuracy(x, y):
    distance = np.sqrt(sum(np.power(a-b, 2) for a, b in zip(x, y)))
    return 1/np.exp(distance)


def average(lst):
    return sum(lst) / len(lst)


def key(info: MediaInfo | CharacterInfo, query: str):
    query_embedding = nlp(query).vector
    if not info:
        return 0
    if isinstance(info, MediaInfo):
        sentence = info.title.preferred
    if isinstance(info, CharacterInfo):
        sentence = info.name.preferred
    similarity = average([accuracy(nlp(word).vector, query_embedding)
                          for word in sentence.split()])
    return similarity * info.popularity


class anime(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(aliases=['sch', 'sall'], help='<query>', description='Search between `character`, `anime`, and `manga`.\n`[Anime]`')
    async def search(self, ctx: commands.Context, *, query: str):
        infos: list[MediaInfo | CharacterInfo] = [
            get_anime(query),
            get_manga(query),
            get_character(query),
        ]
        info = max(
            infos,
            key=lambda x: key(x, query=query)
        )
        if info:
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find anything.')

    @commands.command(name='schar', aliases=['sc'], help='<query>', description='Search character.\n`[Anime]`')
    async def search_character(self, ctx: commands.Context, *, query: str):
        if info := get_character(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find this character.')

    @commands.command(name='sani', aliases=['sa'], help='<query>', description='Search anime.\n`[Anime]`')
    async def search_anime(self, ctx: commands.Context, *, query: str):
        if info := get_anime(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find this anime.')

    @commands.command(name='sman', aliases=['sm'], help='<query>', description='Search manga.\n`[Anime]`')
    async def search_manga(self, ctx: commands.Context, *, query: str):
        if info := get_manga(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find this manga.')


async def setup(client: commands.Bot):
    await client.add_cog(anime(client))
