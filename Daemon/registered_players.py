import asyncio

import coc
from aiohttp import ClientConnectionError

from cogs.utils.custom_player import CustomPlayer


async def update_registered_builder_base_players(daemon, sleep_time: int, is_season_end=False):
    while True:
        try:
            async with daemon.pool.acquire() as conn:
                records = await conn.fetch('''
                                           SELECT coc_tag, discord_member_id FROM RegisteredBuilderBasePlayers
                                           ''')
                try:
                    for [tag, d_member_id] in records:
                        player: CustomPlayer = await daemon.coc_client.get_player(tag, cls=CustomPlayer, db_conn=conn,
                                                                                  season_end=is_season_end)
                        if (await player.has_battled() and d_member_id is not None) or is_season_end:
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
