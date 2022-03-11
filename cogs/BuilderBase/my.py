import typing
from datetime import datetime

import coc
import discord.ui
import matplotlib
import pytz
from discord import Option, OptionChoice, SelectOption
from discord.ext import commands
from matplotlib import pyplot as plt

from cogs.utils.TimePlot import TimePlot

matplotlib.style.use('cogs/utils/neon.mplstyle')

SQL_DICT = {
    'Trophies': 'SELECT time, trophies FROM BuilderBaseBoard WHERE coc_tag = $1 ORDER BY time',
    'Wins': 'SELECT time, wins FROM BuilderBaseBoard WHERE coc_tag = $1 ORDER BY time',
    'Builder Halls': 'SELECT time, builder_halls FROM BuilderBaseBoard WHERE coc_tag = $1 ORDER BY time',
    'Winrate': 'SELECT time, 10 * (wins - FIRST_VALUE(wins) OVER (ORDER BY time ROWS 9 PRECEDING)) '
               'FROM BuilderBaseBoard WHERE coc_tag = $1 ORDER BY time',
    'Trophy Change': 'SELECT time, (trophies - FIRST_VALUE(trophies) OVER (ORDER BY time ROWS 9 PRECEDING)) '
                     'FROM BuilderBaseBoard WHERE coc_tag = $1 ORDER BY time'
}

Y_LABEL_DICT = {
    'Trophies': 'Trophies',
    'Wins': 'Total',
    'Builder Halls': 'Total destroyed builder halls',
    'Winrate': 'Winrate over the last 10 duels respectively in %',
    'Trophy Change': 'Trophy change over the last 10 duels respectively in trophies'
}


class ScrollView(discord.ui.View):
    def __init__(self, plot: TimePlot, user: typing.Union[discord.User, discord.Member]):
        super().__init__()
        self.plot = plot
        self.user = user
        self.message = None
        if len(self.plot.data) > 1:
            select_options = []
            names = []
            for tag, (name, _, _) in self.plot.data.items():
                select_options.append(SelectOption(label=name, description=tag, value=tag))
                names.append(name)
            select_options.insert(0, SelectOption(label='All your accounts', description=', '.join(names),
                                                  value='all accounts'))
            self.account_selector = discord.ui.Select(options=select_options, row=0)
            self.account_selector.callback = self.account_chosen
            self.add_item(self.account_selector)
        self.previous_button = discord.ui.Button(label='◀️', style=discord.ButtonStyle.green, row=1)
        self.previous_button.callback = self.got_to_previous_time_window
        self.add_item(self.previous_button)
        self.next_button = discord.ui.Button(label='▶️', style=discord.ButtonStyle.green, row=1, disabled=True)
        self.next_button.callback = self.got_to_next_time_window
        self.add_item(self.next_button)
        self.now_button = discord.ui.Button(label='⏯️', style=discord.ButtonStyle.green, row=1, disabled=True)
        self.now_button.callback = self.got_to_current_time_window
        self.add_item(self.now_button)
        self.stop_button = discord.ui.Button(label='⏹️', style=discord.ButtonStyle.green, row=1)
        self.stop_button.callback = self.satisfied
        self.add_item(self.stop_button)

    async def got_to_previous_time_window(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user == self.user:
            self.plot.previous()
            await self.update_message(interaction)
        else:
            await interaction.response.send_message('Sorry, only the command user can use these buttons', ephemeral=True)

    async def got_to_next_time_window(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user == self.user:
            self.plot.next()
            await self.update_message(interaction)
        else:
            await interaction.response.send_message('Sorry, only the command user can use these buttons', ephemeral=True)

    async def got_to_current_time_window(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user == self.user:
            self.plot.now()
            await self.update_message(interaction)
        else:
            await interaction.response.send_message('Sorry, only the command user can use these buttons', ephemeral=True)

    async def satisfied(self, interaction: discord.Interaction):
        if interaction.user == self.user:
            self.stop()
        else:
            await interaction.response.send_message('Sorry, only the command user can use these buttons', ephemeral=True)

    async def account_chosen(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user == self.user:
            self.plot.choose_account(self.account_selector.values[0])
            await self.update_message(interaction)
        else:
            await interaction.response.send_message('Sorry, only the command user can use this menu', ephemeral=True)

    async def update_message(self, interaction: discord.Interaction):
        if self.plot.current_end_time - self.plot.offset < self.plot.first_time:
            self.previous_button.disabled = True
        else:
            self.previous_button.disabled = False
        if self.plot.current_end_time + self.plot.offset > datetime.now(self.plot.timezone):
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False
        if self.plot.current_end_time == datetime.now(self.plot.timezone):
            self.now_button.disabled = True
        else:
            self.now_button.disabled = False
        await interaction.delete_original_message()
        self.message = await interaction.followup.send(file=self.plot.plot(), view=self)

    def on_timeout(self) -> None:
        plt.close(self.plot.fig)


class My(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='View graphs how your trophy pushing went')
    async def my(self, ctx: discord.ApplicationContext,
                 which_data: Option(str, name='category',
                                    description='Which data shall I plot over time?',
                                    default='Trophies',
                                    choices=[
                                        OptionChoice('Trophies'),
                                        OptionChoice('Wins'),
                                        OptionChoice('Builder Halls'),
                                        OptionChoice('Winrate'),
                                        OptionChoice('Trophy Change')
                                    ]),
                 time_interval: Option(float, name='time-interval', description='How many days of data do you want to see at once?',
                                       min_value=0.04, max_value=365, default=7.0)
                 ):
        await ctx.defer()
        plot = TimePlot(f'{which_data} of Accounts linked by {ctx.author.display_name}', time_interval, True,
                        Y_LABEL_DICT[which_data], pytz.timezone('UTC'))
        async with self.bot.pool.acquire() as conn:
            tag_records = await conn.fetch('''
                                           SELECT r.coc_tag, t.coc_name
                                           FROM RegisteredBuilderBasePlayers AS r
                                           JOIN TopBuilderBasePlayers AS t ON r.coc_tag = t.coc_tag
                                           WHERE r.discord_member_id = $1
                                           ''',
                                           ctx.author.id)
            if len(tag_records) == 0:
                await ctx.respond('Sorry, I have no data about you. Change that by registering with `/i-am`.')
                return
            nothing_to_show = True
            for record in tag_records:
                tag = record[0]
                name = record[1]
                if which_data == 'season-wins':
                    data_records = await conn.fetch(SQL_DICT[which_data], tag, coc.utils.get_season_start())
                else:
                    data_records = await conn.fetch(SQL_DICT[which_data], tag)
                if len(data_records) > 1:
                    nothing_to_show = False
                times = [record[0] for record in data_records]
                data = [record[1] for record in data_records]
                plot.add_data(tag, name, times, data)
            if nothing_to_show:
                await ctx.respond('Sorry, I have no data to show you. Please do some attacks to change that.')
                return
            image = plot.plot()
        view = ScrollView(plot, ctx.user)
        view.message = await ctx.respond(file=image, view=view)
        await view.wait()
        await view.message.edit(view=None)


def setup(bot):
    bot.add_cog(My(bot))
