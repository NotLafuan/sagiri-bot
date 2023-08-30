import discord
from discord.ui import View, Button
import numpy as np
from time import sleep

EMPTY_CHAR: str = '‎'


class TicTacToe(View):
    def __init__(self, player1: discord.User, player2: discord.User, message: discord.Message, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.message = message
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = np.random.choice(['X', 'O'])
        self.add_buttons()

    async def on_timeout(self) -> None:
        embed = discord.Embed(description=f'Match Timeout!',
                              color=discord.Color.red())
        await self.message.edit(embed=embed, view=self)

    @property
    def buttons(self) -> list[Button]:
        buttons = []
        for index in range(9):
            row, col = self.index_to_row_column(index)
            if label := self.board[row][col]:
                if label == 'X':
                    style = discord.ButtonStyle.red
                elif label == 'O':
                    style = discord.ButtonStyle.blurple
            else:
                label = EMPTY_CHAR
                style = discord.ButtonStyle.grey
            button = Button(label=label, row=row,
                            style=style, custom_id=str(index))
            button.callback = self.button_interaction
            buttons.append(button)
        return buttons

    def add_buttons(self):
        self.clear_items()
        buttons = self.buttons
        for index in range(9):
            self.add_item(buttons[index])

    @property
    def current_user(self) -> discord.User:
        return self.player1 if self.current_player == 'X' else self.player2

    @property
    def current_buttonstyle(self):
        return discord.ButtonStyle.red if self.current_player == 'X' else discord.ButtonStyle.blurple

    @property
    def turn_embed(self) -> discord.Embed:
        color = discord.Color.red() if self.current_player == 'X' else discord.Color.blue()
        return discord.Embed(description=f'{self.current_user.mention}\'s turn', color=color)

    def swap_player(self):
        self.current_player = 'X' if self.current_player == 'O' else 'O'

    def index_to_row_column(self, index: int):
        return index // 3, index % 3

    def fix_spot(self, row: int, col: int):
        self.board[row][col] = self.current_player

    def is_player_win(self, player: str, board: list[list]):
        # checking rows
        for i in range(3):
            win = True
            for j in range(3):
                if board[i][j] != player:
                    win = False
                    break
            if win:
                return win
        # checking columns
        for i in range(3):
            win = True
            for j in range(3):
                if board[j][i] != player:
                    win = False
                    break
            if win:
                return win
        # checking diagonals
        win = True
        for i in range(3):
            if board[i][i] != player:
                win = False
                break
        if win:
            return win
        win = True
        for i in range(3):
            if board[i][3 - 1 - i] != player:
                win = False
                break
        if win:
            return win
        return False

    def is_board_filled(self, board: list[list]):
        for row in board:
            for item in row:
                if not item:
                    return False
        return True

    # AI
    def children_of(self, board: list[list], maximizing_player: bool) -> list[list[list]]:
        children = []
        for i, row in enumerate(board):
            for j, item in enumerate(row):
                if not item:
                    child = np.copy(board)
                    child[i][j] = 'O' if maximizing_player else 'X'
                    children.append(child)
        return children

    def is_player_almost_win(self, player: str, opponent: str) -> int:
        almost_win = 0
        # checking rows
        for i in range(3):
            player_amount = 0
            opponent_amount = 0
            for j in range(3):
                if self.board[i][j] == player:
                    player_amount += 1
                elif self.board[i][j] == opponent:
                    opponent_amount += 1
            if player_amount == 2 and opponent_amount != 1:
                almost_win += 1
        # checking columns
        for i in range(3):
            player_amount = 0
            opponent_amount = 0
            for j in range(3):
                if self.board[j][i] == player:
                    player_amount += 1
                elif self.board[j][i] == opponent:
                    opponent_amount += 1
            if player_amount == 2 and opponent_amount != 1:
                almost_win += 1
        # checking diagonals
        player_amount = 0
        opponent_amount = 0
        for i in range(3):
            if self.board[i][i] == player:
                player_amount += 1
            if self.board[i][i] == opponent:
                opponent_amount += 1
        if player_amount == 2 and opponent_amount != 1:
            almost_win += 1
        player_amount = 0
        opponent_amount = 0
        for i in range(3):
            if self.board[i][3 - 1 - i] == player:
                player_amount += 1
            if self.board[i][3 - 1 - i] == opponent:
                opponent_amount += 1
        if player_amount == 2 and opponent_amount != 1:
            almost_win += 1
        return almost_win

    def evaluation(self, board: list[list]) -> int:
        if self.is_player_win('O', board):
            return 10
        elif self.is_player_win('X', board):
            return -10
        elif self.is_board_filled(board):
            return 0
        else:
            eval = self.is_player_almost_win('X', 'O', board)
            eval -= self.is_player_almost_win('O', 'X', board)
            return eval

    def minimax(self, board: list[list], depth: int, alpha: float, beta: float, maximizing_player: bool):
        if self.is_player_win('X', board) or self.is_player_win('O', board) or self.is_board_filled(board):
            return self.evaluation(board)
        if maximizing_player:
            max_eval = -np.inf
            for child in self.children_of(board, maximizing_player):
                eval = self.minimax(child, depth + 1, alpha, beta, False)
                if eval > max_eval:
                    best_board = child
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            if depth == 0:
                return best_board
            return max_eval
        else:
            min_eval = +np.inf
            for child in self.children_of(board, maximizing_player):
                eval = self.minimax(child, depth + 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def change_index(self, new_board: list[list]):
        for i in range(9):
            row, col = self.index_to_row_column(i)
            if not self.board[row][col] and new_board[row][col]:
                return i

    async def button_interaction(self, interaction: discord.Interaction):
        if interaction.user != self.current_user:
            await interaction.response.send_message(content='Not your turn.', ephemeral=True)
            return
        row, col = self.index_to_row_column(
            int(interaction.data['custom_id']))
        if self.board[row][col]:
            await interaction.response.send_message(
                content='Spot choosen.', ephemeral=True)
            return
        self.fix_spot(row, col)
        self.add_buttons()
        if self.is_player_win(self.current_player, self.board):
            embed = discord.Embed(description=f'{self.current_user.mention} wins the game!',
                                  color=discord.Color.green())
            self.stop()
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.is_board_filled(self.board):
            embed = discord.Embed(description=f'Match Draw!',
                                  color=discord.Color.gold())
            self.stop()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.swap_player()
            await interaction.response.edit_message(embed=self.turn_embed, view=self)
            if self.current_user.bot:
                await self.ai_turn()
                sleep(0.5)

    async def ai_turn(self):
        self.board = self.minimax(self.board, 0, -np.inf, +np.inf, True)
        self.add_buttons()
        if self.is_player_win(self.current_player, self.board):
            embed = discord.Embed(description=f'{self.current_user.mention} wins the game!',
                                  color=discord.Color.green())
            self.stop()
            await self.message.edit(embed=embed, view=self)
        elif self.is_board_filled(self.board):
            embed = discord.Embed(description=f'Match Draw!',
                                  color=discord.Color.gold())
            self.stop()
            await self.message.edit(embed=embed, view=self)
        else:
            self.swap_player()
            await self.message.edit(embed=self.turn_embed, view=self)
