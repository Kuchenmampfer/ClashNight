import asyncio
from datetime import date, datetime

import coc
from aiohttp import ClientConnectionError


async def update_leaderboards(daemon, sleep_time: int, is_season_end=False):
    while True:
        try:
            try:
                leaderboard_global = await daemon.coc_client.get_location_players_versus(limit=200)
                values_global = (date.today(), 'global', [player.tag for player in leaderboard_global],
                                 [player.name for player in leaderboard_global],
                                 [player.versus_trophies for player in leaderboard_global], is_season_end)
                leaderboard_germany = await daemon.coc_client.get_location_players_versus(32000094, limit=200)
                values_germany = (date.today(), 'germany', [player.tag for player in leaderboard_germany],
                                  [player.name for player in leaderboard_germany],
                                  [player.versus_trophies for player in leaderboard_germany], is_season_end)
                leaderboard_clans = await daemon.coc_client.get_location_clans_versus(limit=200)
                values_clans = (date.today(), 'clans', [clan.tag for clan in leaderboard_clans],
                                [clan.name for clan in leaderboard_clans],
                                [clan.versus_points for clan in leaderboard_clans], is_season_end)
            except ClientConnectionError:
                await asyncio.sleep(3600)
                continue
            except coc.Maintenance:
                await asyncio.sleep(3600)
                continue
            async with daemon.pool.acquire() as conn:
                await conn.executemany('''
                                       INSERT INTO BuilderBaseLeaderboards
                                       (record_date, region, tags, names, trophies, is_season_end)
                                       VALUES($1, $2, $3, $4, $5, $6)
                                       ON CONFLICT DO NOTHING
                                       ''',
                                       [values_global, values_germany, values_clans])
                tags = [(player.tag, player.name) for player in leaderboard_global if player.versus_trophies > 6000]
                await conn.executemany('''
                                       INSERT INTO TopBuilderBasePlayers(coc_tag, coc_name)
                                       VALUES($1, $2)
                                       ON CONFLICT DO NOTHING
                                       ''',
                                       tags)
            daemon.logger.info('leaderboards gespeichert und top player registriert')
            if is_season_end:
                break
        except Exception as error:
            daemon.logger.critical(error, exc_info=True)
            exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
            print(exc)
        await asyncio.sleep(sleep_time)


async def update_top_ten(daemon, sleep_time: int):
    while True:
        try:
            try:
                leaderboard_global = await daemon.coc_client.get_location_players_versus()
                leaderboard_global = leaderboard_global[:10]
                values_global = (datetime.now(), 'global', [player.tag for player in leaderboard_global],
                                 [player.name for player in leaderboard_global],
                                 [player.versus_trophies for player in leaderboard_global])
                leaderboard_germany = await daemon.coc_client.get_location_players_versus(32000094, limit=10)
                values_germany = (datetime.now(), 'germany', [player.tag for player in leaderboard_germany],
                                  [player.name for player in leaderboard_germany],
                                  [player.versus_trophies for player in leaderboard_germany])
                leaderboard_clans = await daemon.coc_client.get_location_clans_versus(limit=10)
                values_clans = (datetime.now(), 'clans', [player.tag for player in leaderboard_clans],
                                [player.name for player in leaderboard_clans],
                                [clan.versus_points for clan in leaderboard_clans])
            except ClientConnectionError:
                await asyncio.sleep(600)
                continue
            except coc.Maintenance:
                await asyncio.sleep(600)
                continue
            async with daemon.pool.acquire() as conn:
                await conn.executemany('''
                                       INSERT INTO BuilderBaseTopTen
                                       (time, region, tags, names, trophies)
                                       VALUES($1, $2, $3, $4, $5)
                                       ON CONFLICT DO NOTHING
                                       ''',
                                       [values_global, values_germany, values_clans])
            daemon.logger.debug('top 10 gespeichert')
        except Exception as error:
            daemon.logger.critical(error, exc_info=True)
            exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
            print(exc)
        await asyncio.sleep(sleep_time)
