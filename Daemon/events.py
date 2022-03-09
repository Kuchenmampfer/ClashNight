import asyncio
from datetime import datetime

import coc

from Daemon.leaderboards import update_leaderboards
from cogs.utils.custom_player import CustomPlayer


async def events(daemon):

    @daemon.coc_client.event
    @coc.ClientEvents.new_season_start()
    async def new_season():
        daemon.logger.warning('Uuuund wir haben eine neue season')
        await daemon.update_registered_builder_base_players(1, True)
        daemon.logger.debug('Registered Players updated')
        await daemon.update_leaderboards(1, True)
        daemon.logger.debug('leaderboards updated, the season end event finished successfully :)')
