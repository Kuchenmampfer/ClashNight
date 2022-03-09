import asyncio
from datetime import datetime

import coc
from aiohttp import ClientConnectionError


async def update_trophy_change_analysis(daemon, sleep_time: int):
    old_leaderboard = await daemon.coc_client.get_location_players_versus(limit=200)
    old_tags = set(player.tag for player in old_leaderboard)
    old_trophies_dict = {player.tag: player.versus_trophies for player in old_leaderboard}
    old_places_dict = {player.tag: player.rank for player in old_leaderboard}
    duel_count = 0
    last_minute = datetime.now().minute
    while True:
        try:
            trophy_changes = {}
            try:
                new_leaderboard = await daemon.coc_client.get_location_players_versus(limit=200)
                if new_leaderboard == old_leaderboard:
                    raise ClientConnectionError
            except ClientConnectionError:
                await asyncio.sleep(sleep_time)
                continue
            except coc.Maintenance:
                await asyncio.sleep(sleep_time)
                continue
            new_tags = set(player.tag for player in new_leaderboard)
            new_trophies_dict = {player.tag: player.versus_trophies for player in new_leaderboard}
            new_places_dict = {player.tag: player.rank for player in new_leaderboard}
            for common_tag in old_tags & new_tags:
                trophy_change = abs(new_trophies_dict[common_tag] - old_trophies_dict[common_tag])
                if trophy_change:
                    if trophy_change not in trophy_changes:
                        trophy_changes[trophy_change] = []
                    trophy_changes[trophy_change].append(common_tag)
            duel_count += len([change for change, tags in trophy_changes.items() if len(tags) == 2])

            async with daemon.pool.acquire() as conn:
                await conn.executemany('''
                                       INSERT INTO TrophyChangeAnalysis
                                       (time, previous_places, previous_trophies, trophy_change)
                                       VALUES($1, $2, $3, $4)
                                       ''',
                                       [[datetime.now(), [old_places_dict[tag] for tag in tags],
                                         [old_trophies_dict[tag] for tag in tags], change]
                                        for change, tags in trophy_changes.items() if len(tags) == 2])
                if last_minute > datetime.now().minute:
                    await conn.execute('''
                                       INSERT INTO TopLadderActivity(time, duels)
                                       Values($1, $2)
                                       ''',
                                       datetime.now(), duel_count)
                    duel_count = 0

            old_leaderboard = new_leaderboard
            old_tags = new_tags
            old_trophies_dict = new_trophies_dict
            old_places_dict = new_places_dict
            last_minute = datetime.now().minute
        except Exception as error:
            daemon.logger.critical(error, exc_info=True)
            exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
            print(exc)
        await asyncio.sleep(sleep_time)
