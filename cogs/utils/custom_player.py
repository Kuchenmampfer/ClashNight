from datetime import datetime

import asyncpg
import coc
from coc.miscmodels import try_enum, LegendStatistics


class CustomPlayer(coc.Player):
    """
    This Player class only features the attributes, my daemon is interested in.
    So when using PlayerEvents, he does not cache all the attributes, but only the relevant ones.
    This saves a ton of RAM.
    """

    def __init__(self, data, client, **kwargs):
        self._client: coc.EventsClient = client
        self._database_connection: asyncpg.connection = kwargs.pop("db_conn")
        self.is_season_end: bool = kwargs.pop("season_end")
        self._response_retry = data.get("_response_retry")
        self._from_data(data)

    def _from_data(self, data):
        self.tag = data.get("tag")
        self.name = data.get("name")
        self.versus_trophies = data.get("versusTrophies")
        self.best_versus_trophies = data.get("bestVersusTrophies")
        self.versus_attack_wins = data.get("versusBattleWins")
        self.legend_statistics = try_enum(LegendStatistics, data=data.get("legendStatistics"))

        for achievement in data.get("achievements"):
            if achievement["name"] == "Un-Build It":
                self.builder_halls_destroyed = achievement["value"]

    async def has_battled(self):
        record = await self._database_connection.fetchrow('''
                                                          SELECT trophies FROM BuilderBaseBoard
                                                          WHERE coc_tag = $1
                                                          ORDER BY time DESC
                                                          LIMIT 1
                                                          ''',
                                                          self.tag
                                                          )
        previous_versus_trophies = record[0]
        return self.versus_trophies != previous_versus_trophies

    async def save_to_bb_board(self):
        await self._database_connection.execute('''
                                                INSERT INTO BuilderBaseBoard
                                                (time, coc_tag, trophies, wins, builder_halls, is_season_end)
                                                VALUES($1, $2, $3, $4, $5, $6)
                                                ''',
                                                datetime.now(), self.tag, self.versus_trophies,
                                                self.versus_attack_wins, self.builder_halls_destroyed,
                                                self.is_season_end
                                                )

    async def save_previous_season(self):
        previous_season = self.legend_statistics.previous_versus_season
        await self._database_connection.execute('''
                                                INSERT INTO BuilderBaseFinishes
                                                (coc_tag, finish_season_id, finish_rank, finish_trophies)
                                                VALUES($1, $2, $3, $4)
                                                ON CONFLICT DO NOTHING
                                                ''',
                                                self.tag,
                                                previous_season.id, previous_season.rank, previous_season.trophies
                                                )

    async def update_legend_cups(self):
        await self._database_connection.execute('''
                                                UPDATE RegisteredBuilderBasePlayers
                                                SET legend_cups = legend_cups + $2
                                                WHERE coc_tag = $1
                                                ''',
                                                self.tag, max(self.versus_trophies - 5000, 0))
