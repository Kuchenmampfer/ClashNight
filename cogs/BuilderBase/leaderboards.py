from typing import Dict, Union, Any, Optional

import coc
import discord
from discord import Option, OptionChoice
from discord.ext import commands

from cogs.utils.leaderboard import Leaderboard

#  the following part reads the locations available at the coc api and makes them available for slash command use.
with open('locations.csv', 'r', encoding='utf-8') as f:
    LOCATIONS = ['Global']
    LOCATION_DICT: dict[str, Optional[int]] = {'Global': None}
    for line in f.readlines():
        loc, loc_id = line.split(',')
        LOCATIONS.append(loc)
        LOCATION_DICT[loc] = int(loc_id)


def get_location(ctx: discord.AutocompleteContext):
    return [location for location in LOCATIONS if location.lower().startswith(ctx.value.lower())]


# little trick, to make an object from a dict
class Objectify(object):
    def __init__(self, data: dict):
        self.__dict__ = data


class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='leaderboard', description='Get a live leaderboard from any location')
    async def leaderboard(self,
                          ctx: discord.ApplicationContext,
                          location: Option(str,
                                           'Choose the location you want the leaderboard of. Default: Global',
                                           default='Global',
                                           autocomplete=get_location
                                           ),
                          mode: Option(str,
                                       'Do you want the player or clan leaderboard? Default: Players',
                                       choices=['Players', 'Clans'],
                                       default='Players'
                                       )

                          ):
        await ctx.defer()
        if mode == 'Players':
            leaderboard_list: list[coc.RankedPlayer] = \
                await self.bot.coc.get_location_players_versus(LOCATION_DICT[location]) \
                if LOCATION_DICT[location] \
                else await self.bot.coc.get_location_players_versus()
            leaderboard = Leaderboard(leaderboard_list,
                                      f'Leaderboard in {location}',
                                      '{0}{1}`{2.versus_trophies}`🏆 {2.name}\n',
                                      True
                                      )
        else:
            leaderboard_list: list[coc.RankedClan] = \
                await self.bot.coc.get_location_clans_versus(LOCATION_DICT[location]) \
                if LOCATION_DICT[location] \
                else await self.bot.coc.get_location_clans_versus()
            leaderboard = Leaderboard(leaderboard_list,
                                      f'Clan leaderboard in {location}',
                                      '{0}{1}`{2.versus_points}`🏆 {2.name}\n',
                                      True
                                      )
        await leaderboard.respond(ctx.interaction)

    @commands.slash_command(name='server-leaderboard',
                            description='Get a leaderboard with all the players in this discord server')
    async def server_leaderboard(self,
                                 ctx: discord.ApplicationContext,
                                 category: Option(int,
                                                  'In wich category shall I rank the server members? Default: Trophies',
                                                  choices=[
                                                      OptionChoice('Trophies', 5),
                                                      OptionChoice('All time best', 0),
                                                      OptionChoice('Best finish season', 1),
                                                      OptionChoice('Best finish rank', 2),
                                                      OptionChoice('Best finish trophies', 3),
                                                      OptionChoice('Number of wins', 6),
                                                      OptionChoice('Number of builder halls destroyed', 7)
                                                  ],
                                                  default=5
                                                  ),
                                 ):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            records = await conn.fetch(
                '''
                SELECT * FROM FullCocPlayers
                WHERE coc_tag IN
                (
                    SELECT coc_tag FROM RegisteredBuilderBasePlayers
                    WHERE discord_member_id IN
                    (
                        SELECT member_id FROM GuildMemberReferences
                        WHERE guild_id = $1
                    )
                )
                ''',
                ctx.guild_id
            )
            if len(records) == 0:
                await ctx.respond('No one in this server has linked any account. To use this command, please register '
                                  'using the `/i-am´ command.')

            leaderboard_list = []
            for record in records:
                dict_player = dict(record)
                dict_player['sort_by'] = record[category + 2]
                if not dict_player['sort_by']:
                    continue
                player = Objectify(dict_player)
                leaderboard_list.append(player)
            leaderboard_list.sort(key=lambda x: x.sort_by, reverse=category in [0, 3, 4, 5, 6, 7])

        format_strings = [
            '{0}`{1.best_versus_trophies}`🏆 {1.coc_name}\n',
            '{0}`{1.best_season_id}`🗓️ `{1.best_season_rank:4}`🪜 `{1.best_season_trophies}`🏆 {1.coc_name}\n',
            '{0}`{1.best_season_id}`🗓️ `{1.best_season_rank:4}`🪜 `{1.best_season_trophies}`🏆 {1.coc_name}\n',
            '{0}`{1.best_season_id}`🗓️ `{1.best_season_rank:4}`🪜 `{1.best_season_trophies}`🏆 {1.coc_name}\n',
            '{0}`{1.legend_cups}`🏅 {1.coc_name}\n',
            '{0}`{1.trophies}`🏆 {1.coc_name}\n',
            '{0}`{1.wins}`🎯 {1.coc_name}\n',
            '{0}`{1.builder_halls}`🛖 {1.coc_name}\n',
        ]

        header_categories = [
            'All time best',
            'Best finish season',
            'Best finish rank',
            'Best finish trophies',
            'Prestige',
            'Trophy',
            'Number of wins',
            'Number of builder halls destroyed',
        ]

        leaderboard = Leaderboard(leaderboard_list,
                                  f'{header_categories[category]} leaderboard in {ctx.guild.name}',
                                  format_strings[category],
                                  False
                                  )
        await leaderboard.respond(ctx.interaction)


def setup(bot):
    bot.add_cog(Leaderboards(bot))
