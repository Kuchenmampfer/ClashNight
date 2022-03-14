import discord

from cogs.utils import functions


class Leaderboard(discord.ui.View):
    def __init__(self, user_id: int, leaderboard_list: list, header: str, format_string: str, show_arrows: bool):
        self.user_id = user_id
        self.list = leaderboard_list
        self.format_string = format_string
        self.current_embed_index = 0

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

        self.top_button = discord.ui.Button(label='⏫', style=discord.ButtonStyle.green, disabled=True)
        self.top_button.callback = self.go_to_the_top
        self.previous_button = discord.ui.Button(label='🔼', style=discord.ButtonStyle.green, disabled=True)
        self.previous_button.callback = self.go_to_previous
        self.next_button = discord.ui.Button(label='🔽', style=discord.ButtonStyle.green)
        self.next_button.callback = self.go_to_next
        self.bottom_button = discord.ui.Button(label='⏬', style=discord.ButtonStyle.green,
                                               disabled=self.current_embed_index > len(self.embeds)-3)
        self.bottom_button.callback = self.go_to_last
        super().__init__(self.top_button, self.previous_button, self.next_button, self.bottom_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message("Sorry, only the command user can use these buttons", ephemeral=True)
        return False

    async def go_to_the_top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index = 0
        await self.update_leaderboard(interaction)

    async def go_to_previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index -= 1
        await self.update_leaderboard(interaction)

    async def go_to_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index += 1
        await self.update_leaderboard(interaction)

    async def go_to_last(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index = len(self.embeds) - 1
        await self.update_leaderboard(interaction)

    async def disable_buttons(self):
        self.top_button.disabled = self.current_embed_index < 2
        self.previous_button.disabled = self.current_embed_index < 1
        self.next_button.disabled = self.current_embed_index > len(self.embeds) - 2
        self.bottom_button.disabled = self.current_embed_index > len(self.embeds) - 3

    async def update_leaderboard(self, interaction: discord.Interaction):
        await self.disable_buttons()
        await interaction.edit_original_message(embed=self.embeds[self.current_embed_index],
                                                view=self if len(self.embeds) > 1 else None)
