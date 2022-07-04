import discord
from discord.ext import commands
import numpy as np
from utils import *


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
            icon_url=ctx.author.avatar.url,
            text=f'Asked by {ctx.author.display_name}'
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.group(aliases=['ttt'], invoke_without_command=True, help='<user>', description='Create a tictactoe match.\n`[Extra]`')
    async def tictactoe(self, ctx: commands.Context, user: discord.User):
        player1 = ctx.author
        player2 = user

        if not player2.bot:
            embed = discord.Embed(description=f'{player1.mention} vs {player2.mention}',
                                  color=SILVER)
            confirm = Button(label='✔️', style=discord.ButtonStyle.green)
            decline = Button(label='❌', style=discord.ButtonStyle.red)

            async def confirm_callback(interaction: discord.Interaction):
                embed = discord.Embed(description=f'{player1.mention} vs {player2.mention} Confirmed!',
                                      color=SILVER)
                tictactoe = TicTacToe(player1, player2, interaction.message)
                await interaction.response.edit_message(embed=tictactoe.turn_embed, view=tictactoe)

            async def decline_callback(interaction: discord.Interaction):
                embed = discord.Embed(description=f'{player1.mention} vs {player2.mention} Cancelled.',
                                      color=SILVER)
                await interaction.response.edit_message(embed=embed, view=None)
            confirm.callback = confirm_callback
            decline.callback = decline_callback
            view = View()
            view.add_item(confirm)
            view.add_item(decline)
            await ctx.send(embed=embed, view=view)
        else:
            await send_notice(ctx, 'Cannot play with bot.')

    @tictactoe.command(name='ai', aliases=['bot'], help='', description='Tictactoe against Sagiri.\n`[Extra]`')
    async def tictactoe_ai(self, ctx: commands.Context):
        player1 = ctx.author
        player2 = self.client.user

        embed = discord.Embed(description=f'{player1.mention} vs {player2.mention}',
                              color=SILVER)
        message: discord.Message = await ctx.send(embed=embed)
        tictactoe = TicTacToe(player1, player2, message)
        if tictactoe.current_user == player2:
            await tictactoe.ai_turn()
        await message.edit(embed=tictactoe.turn_embed, view=tictactoe)


async def setup(client: commands.Bot):
    await client.add_cog(extra(client))
