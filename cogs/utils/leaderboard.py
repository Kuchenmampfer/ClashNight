import discord
from discord.ext import pages

from cogs.utils import functions


class Leaderboard(pages.Paginator):
    def __init__(self, leaderboard_list: list, header: str, format_string: str, show_arrows: bool):
        self.list = leaderboard_list
        self.format_string = format_string

        self.embeds: list[discord.Embed] = []
        for i in range(len(leaderboard_list)):
            rank = functions.place_emote(i + 1)
            if i % 20 == 0:
                self.embeds.append(discord.Embed(title=header, description='', colour=discord.Colour.blue()))
            if show_arrows:
                arrow = functions.get_direction_arrow(self.list[i].rank, self.list[i].previous_rank)
                self.embeds[-1].description += self.format_string.format(rank, arrow, self.list[i])
            else:
                self.embeds[-1].description += self.format_string.format(rank, self.list[i])

        self.buttons = [
            pages.PaginatorButton('first', label='⏫', style=discord.ButtonStyle.green),
            pages.PaginatorButton('prev', label='🔼', style=discord.ButtonStyle.green),
            pages.PaginatorButton('next', label='🔽', style=discord.ButtonStyle.green),
            pages.PaginatorButton('last', label='⏬', style=discord.ButtonStyle.green),

        ]

        super().__init__(self.embeds, use_default_buttons=False, custom_buttons=self.buttons, show_indicator=False,
                         timeout=60)

