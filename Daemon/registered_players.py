import asyncio

import coc
from aiohttp import ClientConnectionError

from cogs.utils.custom_player import CustomPlayer


async def update_registered_builder_base_players(daemon, sleep_time: int, is_season_end=False):
    while True:
        try:
            async with daemon.pool.acquire() as conn:
                records = await conn.fetch('''
                                           SELECT coc_tag FROM RegisteredBuilderBasePlayers
                                           WHERE discord_member_id IS NOT NULL
                                           ''')
                db_player_tags = [record[0] for record in records]
                try:
                    for tag in db_player_tags:
                        player: CustomPlayer = await daemon.coc_client.get_player(tag, cls=CustomPlayer,
                                                                                  db_conn=conn, season_end=is_season_end)
                        if await player.has_battled() or is_season_end:
                            await player.save_to_bb_board()
                        if is_season_end:
                            await player.update_legend_cups()
                        try:
                            await player.save_previous_season()
                        except AttributeError:
                            continue
                except ClientConnectionError:
                    pass
                except coc.Maintenance:
                    pass

            if is_season_end:
                break
        except Exception as error:
            daemon.logger.critical(error, exc_info=True)
        await asyncio.sleep(sleep_time)
