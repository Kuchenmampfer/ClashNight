import asyncio

import coc
from aiohttp import ClientConnectionError


async def update_top_builder_base_players(daemon, sleep_time: int):
    while True:
        try:
            async with daemon.pool.acquire() as conn:
                records = await conn.fetch('''
                                           SELECT coc_tag FROM TopBuilderBasePlayers
                                           ''')
                db_player_tags = [record[0] for record in records]
                try:
                    for tag in db_player_tags:
                        try:
                            player = await daemon.coc_client.get_player(tag)
                            try:
                                best_season = player.legend_statistics.best_versus_season
                                season_id = best_season.id
                                season_rank = best_season.rank
                                season_trophies = best_season.trophies
                                await conn.execute('''
                                                   UPDATE TopBuilderBasePlayers
                                                   SET coc_name = $2, best_versus_trophies = $3,
                                                   best_season_id = $4, best_season_rank = $5, best_season_trophies = $6
                                                   WHERE coc_tag = $1
                                                   ''',
                                                   player.tag, player.name, player.best_versus_trophies,
                                                   season_id, season_rank, season_trophies)
                            except BaseException:
                                await conn.execute('''
                                                   UPDATE TopBuilderBasePlayers
                                                   SET coc_name = $2, best_versus_trophies = $3
                                                   WHERE coc_tag = $1
                                                   ''',
                                                   player.tag, player.name, player.best_versus_trophies)
                        except coc.errors.NotFound:
                            await conn.execute('''
                                                DELETE FROM TopBuilderBasePlayers 
                                                WHERE coc_tag = $1
                                                ''', tag)
                    daemon.logger.info('Namen, best seasons und Pokalrekorde aktualisiert')
                except ClientConnectionError:
                    pass
                except coc.Maintenance:
                    pass

        except Exception as error:
            daemon.logger.critical(error, exc_info=True)
        await asyncio.sleep(sleep_time)
