import asyncio
import asyncpg

from Daemon.events import events
from Daemon.leaderboards import update_leaderboards, update_top_ten
from Daemon.registered_players import update_registered_builder_base_players
from Daemon.top_bb_players import update_top_builder_base_players
from Daemon.trophy_change_analysis import update_trophy_change_analysis
from log_stuff.logger_setup import setup_logger
from settings import Settings


class Daemon:
    def __init__(self, settings: Settings):
        self.coc_client = settings.coc_client
        self.postgres_dsn_str = settings.dsn
        self.logger = setup_logger('logger', 'log_stuff/daemon.log', settings.webhook_url, settings.log_level)
        self.coc_logger = setup_logger('coc.http', 'log_stuff/demon_coc.log', settings.webhook_url, settings.log_level)

    def exception_handler(self, _, context: dict):
        message = context['message']
        context.pop('message')
        self.logger.critical(msg=message, **context)

    async def start(self):
        """Async start point will for all background tasks"""
        self.pool: asyncpg.pool.Pool = await asyncpg.create_pool(self.postgres_dsn_str)
        self.logger.warning("Pool initiated")
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(self.exception_handler)

        tasks = [
            loop.create_task(self.update_trophy_change_analysis(60)),
            loop.create_task(self.update_registered_builder_base_players(60)),
            loop.create_task(self.update_top_ten(3600)),
            loop.create_task(self.update_top_builder_base_players(86400)),
            loop.create_task(self.update_leaderboards(86400)),
            loop.create_task(self.events())
        ]
        await asyncio.wait(tasks)

    async def update_trophy_change_analysis(self, sleep_time: int):
        await update_trophy_change_analysis(self, sleep_time)

    async def update_leaderboards(self, sleep_time: int, is_season_end=False):
        await update_leaderboards(self, sleep_time, is_season_end)

    async def update_top_ten(self, sleep_time: int):
        await update_top_ten(self, sleep_time)

    async def update_top_builder_base_players(self, sleep_time: int):
        await update_top_builder_base_players(self, sleep_time)

    async def update_registered_builder_base_players(self, sleep_time: int, is_season_end=False):
        await update_registered_builder_base_players(self, sleep_time, is_season_end)

    async def events(self):
        await events(self)

