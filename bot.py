import asyncio
import traceback
from abc import ABC
from time import sleep

import asyncpg
import coc
import discord
from discord.ext import commands

from log_stuff.logger_setup import setup_logger
from settings import Settings


class Bot(commands.Bot, ABC):
    def __init__(self, settings: Settings):
        super().__init__(command_prefix=',',
                         case_insensitive=True,
                         intents=settings.intents,
                         help_command=None,
                         activity=discord.Game('/info for information'))
        self.coc = settings.coc_client
        self.emotes = settings.emotes
        self.war_report_channel_id = settings.war_report_channel_id
        self.logger = setup_logger('logger', 'log_stuff/my.log', settings.webhook_url, settings.log_level)
        self.discord_logger = setup_logger('discord', 'log_stuff/discord.log', settings.webhook_url, settings.log_level)
        self.coc_logger = setup_logger('coc.http', 'log_stuff/coc.log', settings.webhook_url, settings.log_level)
        self.postgres_dsn_str = settings.dsn
        self.pool = None
        asyncio.get_event_loop().run_until_complete(self.get_pool())
        sleep(4)

        for extension in settings.cogs:
            try:
                self.load_extension(extension)
            except BaseException as error:
                exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
                self.logger.error(exc)

    async def get_pool(self):
        self.pool = await asyncpg.create_pool(self.postgres_dsn_str)

    async def on_ready(self):
        self.logger.warning(f"Bot is logged in as {self.user} ID: {self.user.id}")
        async with self.pool.acquire() as conn:
            for guild in self.guilds:
                await conn.execute('''
                                           INSERT INTO DiscordGuilds(guild_id, guild_name)
                                           VALUES($1, $2)
                                           ON CONFLICT DO NOTHING
                                           ''',
                                   guild.id, guild.name)
                async for member in guild.fetch_members():
                    if not member.bot:
                        await conn.execute('''
                                                   INSERT INTO DiscordMembers(member_id, member_name)
                                                   VALUES($1, $2)
                                                   ON CONFLICT DO NOTHING
                                                   ''',
                                           member.id, member.name)
                        await conn.execute('''
                                                   INSERT INTO GuildMemberReferences(guild_id, member_id)
                                                   VALUES($1, $2)
                                                   ON CONFLICT DO NOTHING
                                                   ''',
                                           guild.id, member.id)
        self.logger.warning('Guilds and members updated')

    async def on_resume(self):
        self.logger.warning('Resuming connection...')

    async def on_application_command_error(
            self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        if isinstance(error, coc.errors.Maintenance):
            await ctx.respond('The clash of clans api currently is in maintenance. Please try again later.')
        elif isinstance(error, asyncio.exceptions.TimeoutError):
            await ctx.respond('It seems like the clash of clans api has some problems. Please try again later.')
        else:
            await ctx.respond('Ooops, something went wrong. I informed my developer so he can fix it.')
        exc = ctx.command.qualified_name
        exc += ' caused the following error:\n'
        exc += ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
        self.logger.error(exc)
