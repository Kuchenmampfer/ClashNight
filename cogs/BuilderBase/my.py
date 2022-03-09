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
    def __init__(self, plot: TimePlot):
        super().__init__()
        self.plot = plot
        self.message = None
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

    @discord.ui.button(label='◀️', style=discord.ButtonStyle.green, row=1)
    async def got_to_previous_time_window(self, _: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.plot.previous()
        await self.update_message(interaction)

    @discord.ui.button(label='▶️', style=discord.ButtonStyle.green, row=1)
    async def got_to_next_time_window(self, _: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.plot.next()
        await self.update_message(interaction)

    @discord.ui.button(label='⏯️', style=discord.ButtonStyle.green, row=1)
    async def got_to_current_time_window(self, _: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.plot.now()
        await self.update_message(interaction)

    @discord.ui.button(label='⏹️', style=discord.ButtonStyle.green, row=1)
    async def satisfied(self, _: discord.ui.Button, __: discord.Interaction):
        self.stop()

    async def account_chosen(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.plot.chosen_account = self.account_selector.values[0]
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
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
            for record in tag_records:
                tag = record[0]
                name = record[1]
                if which_data == 'season-wins':
                    data_records = await conn.fetch(SQL_DICT[which_data], tag, coc.utils.get_season_start())
                else:
                    data_records = await conn.fetch(SQL_DICT[which_data], tag)
                times = [record[0] for record in data_records]
                data = [record[1] for record in data_records]
                plot.add_data(tag, name, times, data)
            image = plot.plot()
        view = ScrollView(plot)
        view.message = await ctx.respond(file=image, view=view)
        await view.wait()
        await view.message.edit(view=None)


def setup(bot):
    bot.add_cog(My(bot))
