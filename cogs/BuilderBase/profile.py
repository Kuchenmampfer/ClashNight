import asyncpg
import coc
import discord
from coc.miscmodels import Season
from discord import Option
from discord.ext import commands

from bot import Bot


class Dropdown(discord.ui.Select):
    def __init__(self, bot: Bot, member: discord.Member, accounts: dict):
        self.bot = bot
        self.member = member
        options = [discord.SelectOption(label="Overview", value="all",
                                        description="Shows an overview over all your accounts")]
        for tag, name in accounts.items():
            options.append(discord.SelectOption(label=name, value=tag, description=tag))
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.bot.pool.acquire() as conn:
            if self.values[0] == "all":
                embed = discord.Embed(title=f'Accounts from {self.member.display_name}',
                                      colour=discord.Colour.blue(), )
                embed.set_thumbnail(url=self.member.display_avatar.url)
                coc_account_records = await get_accounts_data(conn, self.member.id)
                await add_accounts_overview(embed, coc_account_records)
            else:
                data = await get_account_data(conn, self.values[0])
                embed = get_account_embed(data, self.member.display_avatar.url)
            await interaction.edit_original_message(embed=embed, view=self.view)


async def get_accounts_data(conn: asyncpg.Connection, discord_id: int) -> list[asyncpg.Record]:
    coc_account_records = await conn.fetch('''
                                           SELECT * FROM FullCocPlayers
                                           WHERE coc_tag IN (
                                               SELECT coc_tag FROM RegisteredBuilderBasePlayers
                                               WHERE discord_member_id = $1
                                               )
                                           ORDER BY best_season_rank, best_versus_trophies
                                           ''',
                                           discord_id)
    return coc_account_records


async def get_account_data(conn: asyncpg.Connection, tag: str) -> dict:
    standard_record = await conn.fetchrow('SELECT * FROM FullCocPlayers WHERE coc_tag = $1', tag)
    data = dict(standard_record)
    finishes = await conn.fetch('''
                                SELECT * FROM BuilderBaseFinishes
                                WHERE coc_tag = $1
                                ORDER BY finish_season_id DESC
                                ''', tag)
    seasons = []
    for record in finishes:
        season_dict = {"id": record[1], "rank": record[2], "trophies": record[3]}
        season = Season(data=season_dict)
        seasons.append(season)
    data["seasons"] = seasons
    try:
        season_statistics = await conn.fetchrow('''
                                                SELECT MAX(trophies) season_high,
                                                (MAX(wins) - MIN(wins)) season_wins,
                                                100 * (MAX(wins) - MIN(wins)) / (COUNT(*) - 1) season_winrate
                                                FROM BuilderBaseBoard
                                                WHERE coc_tag = $1 AND
                                                time BETWEEN (
                                                         SELECT MIN(time)
                                                         FROM BuilderBaseBoard
                                                         WHERE coc_tag = $1
                                                         AND trophies = 5000
                                                         AND time >= (
                                                             SELECT MAX(time)
                                                             FROM BuilderBaseBoard
                                                             WHERE coc_tag = $1 AND
                                                             is_season_end = TRUE
                                                             )
                                                         ) AND
                                                     NOW()
                                                ''', tag)
        for key, val in season_statistics.items():
            data[key] = val
    except asyncpg.exceptions.DivisionByZeroError:
        pass
    return data


async def add_accounts_overview(embed: discord.Embed, coc_account_records: list[asyncpg.Record]) -> None:
    for record in coc_account_records:
        value = f'[{record[0]}](https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=%23{record[0]})\n' \
                f'`{record[7]}`:trophy:`{record[2]}`⛰️`{record[8]:5}`:dart:`{record[9]:5}`:hut:\n' \
                f'-------------------------------------------'

        embed.add_field(name=record[1],
                        value=value,
                        inline=False)


def get_account_embed(data: dict, member_avatar_url: str = '') -> discord.Embed:
    embed = discord.Embed(title=data["coc_name"],
                          description=f'[{data["coc_tag"]}](https://link.clashofclans.com/en?action=OpenPlayerProfile&'
                                      f'tag=%23{data["coc_tag"][1:]})',
                          colour=discord.Colour.blue())
    if member_avatar_url:
        embed.set_thumbnail(url=member_avatar_url)
    value = f'`{data["trophies"]:7}`:trophy: `{data["wins"]:6}`:dart: `{data["builder_halls"]:5}`:hut:'
    embed.add_field(name="Current Scores", value=value, inline=False)
    value = f'`{data["best_versus_trophies"]:7}`:mountain:'
    embed.add_field(name="All time high", value=value, inline=False)
    try:
        value = f'`{data["season_high"]:7}`:mountain: `{data["season_wins"]:6}`:dart: ' \
                f'`{data["season_winrate"]:4}%`:chart_with_upwards_trend:'
        embed.add_field(name='Current season: high, wins, winrate', value=value, inline=False)
    except KeyError:
        pass
    except TypeError:
        pass
    value = ""
    for season in data["seasons"]:
        if season.rank == min([season.rank for season in data["seasons"]]):
            add = ":fire:"
        else:
            add = ""
        value += f'`{season.id:7}`:calendar_spiral: `{season.rank:6}`:ladder: `{season.trophies:5}`:trophy: {add}\n'
    if value:
        embed.add_field(name="Finishes", value=value, inline=False)
    return embed


async def create_embed(member: discord.Member, coc_account_records: list[asyncpg.Record]) -> discord.Embed:
    embed = discord.Embed(title=f'Accounts from {member.display_name}', colour=discord.Colour.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    await add_accounts_overview(embed, coc_account_records)
    return embed


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.user_command(name="builder-base-profile",
                           description='View details on all coc accounts linked to a discord user')
    async def user_profile(self, ctx: discord.ApplicationContext, member: discord.Member):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            coc_account_records = await get_accounts_data(conn, member.id)
            if len(coc_account_records) == 0:
                await ctx.respond('Sorry, I have no data about this user. He can change that by registering with '
                                  '`/i-am`.')
                return
            if len(coc_account_records) == 1:
                data = await get_account_data(conn, coc_account_records[0][0])
                embed = get_account_embed(data, member.display_avatar.url)
            else:
                embed = await create_embed(member, coc_account_records)
        accounts = {}
        for record in coc_account_records:
            accounts[record["coc_tag"]] = record["coc_name"]
        view = discord.ui.View(Dropdown(self.bot, member, accounts))
        message = await ctx.respond(embed=embed, view=view)
        await view.wait()
        await message.edit(view=None)

    @commands.slash_command(name="profile", description='View details on all coc accounts linked to a discord user')
    async def slash_profile(self, ctx: discord.ApplicationContext,
                            member: Option(discord.Member, "From who do you want to see the profile?")):
        await self.user_profile(self, ctx, member)

    @commands.slash_command(name='player', description='View details about a clash of clans player', )
    async def player_info(self, ctx: discord.ApplicationContext,
                          player_tag: Option(str, 'The in game tag of the player I shall show')):
        await ctx.defer()
        try:
            player: coc.Player = await self.bot.coc.get_player(player_tag)
        except coc.NotFound:
            await ctx.respond(f'Sorry, I could not find any player with the tag {player_tag}.')
            return
        data = {
            'coc_name': player.name,
            'coc_tag': player.tag,
            'trophies': player.versus_trophies,
            'wins': player.versus_attack_wins,
            'builder_halls': player.get_achievement('Un-Build It').value,
            'best_versus_trophies': player.best_versus_trophies,
            'seasons': []
        }
        try:
            if player.legend_statistics.previous_versus_season is None:
                raise AttributeError
            data['seasons'].append(player.legend_statistics.previous_versus_season)
        except AttributeError:
            pass
        try:
            if player.legend_statistics.previous_versus_season is None:
                raise AttributeError
            data['seasons'].append(player.legend_statistics.best_versus_season)
        except AttributeError:
            pass
        embed = get_account_embed(data)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Profile(bot))
