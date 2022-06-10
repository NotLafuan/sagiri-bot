import discord
from discord.ext import commands
import numpy as np
from utils import send_notice, MESSAGE, SILVER


class extra(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(name='8ball', aliases=['8_ball', '8', 'ball', '🎱'], help='<question>', description='Ask Sagiri to do prediction.\n`[Extra]`')
    async def _8ball(self, ctx: commands.Context, *, question: str):
        # responses
        yeses = [
            'It is certain.',
            'It is decidedly so.',
            'Without a doubt.',
            'Yes - definitely.',
            'You may rely on it.',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good.',
            'Yes.',
            'Yes - definitely.',
            'Signs point to yes.',
            'Yes definitely.',
            'Most likely.'
        ]
        nos = [
            'Don\'t count on it.',
            'My sources say no.',
            'Outlook not so good.',
            'Very doubtful.',
            'My reply is no',
            'No.'
        ]
        idks = [
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.'
        ]

        if (choice := np.random.random()) <= 0.45:
            response = np.random.choice(yeses)
        elif choice > 0.45 and choice <= .9:
            response = np.random.choice(nos)
        else:
            response = np.random.choice(idks)

        # question bar
        empty_length = 37 - len(question)
        if empty_length > 0:
            question = question + ' '*empty_length
        question = f'`{question}`'

        # response bar
        empty_length = 37 - len(response)
        if empty_length > 0:
            response = response + ' '*empty_length
        response = f'`{response}`'

        embed = discord.Embed(
            title='8 Ball',
            description=question,
            color=SILVER
        )
        embed.add_field(name='Prediction', value=response)
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f'Asked by {ctx.author.display_name}'
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)


def setup(client: commands.Bot):
    client.add_cog(extra(client))
