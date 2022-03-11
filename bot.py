import sys

import asyncpg
import coc
import discord
import traceback
import asyncio

from discord.ext import commands
from time import sleep

from log_stuff.logger_setup import setup_logger
from settings import Settings


class Bot(commands.Bot):
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
        for guild in self.guilds:
            async with self.pool.acquire() as conn:
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

    async def on_ready(self):
        self.logger.warning(f"Bot is logged in as {self.user} ID: {self.user.id}")

    async def on_resume(self):
        self.logger.warning('Resuming connection...')

    async def on_command(self, ctx):
        await ctx.trigger_typing()
        self.logger.debug(f'{ctx.author} hat {ctx.message.content} aufgerufen.')

    async def on_command_error(self, ctx, error):
        if isinstance(error, coc.errors.Maintenance):
            await ctx.send('Die API ist gerade in der Wartungspause, probier es später nochmal')
        elif isinstance(error, commands.errors.CommandNotFound):
            pass
        else:
            exc = f'Command "{ctx.message.content}" caused the following error:\n\n' + \
                  ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
            self.logger.error(exc)

    async def on_application_command_error(
            self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        if isinstance(error, coc.errors.Maintenance):
            await ctx.respond('Die API ist gerade in der Wartungspause, probier es später nochmal')
        else:
            exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=True))
            self.logger.error(exc)
