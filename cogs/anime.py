from discord.ext import commands
from math import sqrt, pow, exp
from utils import *

import spacy
nlp = spacy.load('en_core_web_sm')


def accuracy(x, y):
    distance = sqrt(sum(pow(a-b, 2) for a, b in zip(x, y)))
    return 1/exp(distance)


def average(lst):
    return sum(lst) / len(lst)


def key(info: Optional[MediaInfo | CharacterInfo], query: str):
    query_embedding = nlp(query).vector
    if info:
        if isinstance(info, MediaInfo):
            sentence = info.title.preferred
        if isinstance(info, CharacterInfo):
            sentence = info.name.preferred
        similarity = average([accuracy(nlp(word).vector, query_embedding)
                              for word in sentence.split()])
        return similarity * info.popularity
    else:
        return 0


class anime(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(aliases=['sch', 'sall'], help='')
    async def search(self, ctx: commands.Context, *, query: str):
        infos: list[Optional[MediaInfo | CharacterInfo]] = [
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

    @commands.command(name='schar', aliases=['sc'], help='')
    async def search_character(self, ctx: commands.Context, *, query: str):
        if info := get_character(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find for this character.')

    @commands.command(name='sani', aliases=['sa'], help='')
    async def search_anime(self, ctx: commands.Context, *, query: str):
        if info := get_anime(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find for this anime.')

    @commands.command(name='sman', aliases=['sm'], help='')
    async def search_manga(self, ctx: commands.Context, *, query: str):
        if info := get_manga(query):
            await ctx.send(embed=info.embed)
        else:
            await send_notice(ctx, 'Unable to find for this manga.')


def setup(client: commands.Bot):
    client.add_cog(anime(client))
