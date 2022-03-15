from datetime import datetime

import asyncpg
import coc
from coc.miscmodels import Season
from discord import ApplicationContext, Option
from discord.ext import commands

from cogs.utils import functions


async def respond_or_send(ctx, is_slash_command: bool, message: str) -> None:
    if is_slash_command:
        await ctx.respond(message)
    else:
        await ctx.send(message)


def get_seasons(player: coc.Player) -> [bool, Season, Season]:
    try:
        has_seasons = True
        best_season = player.legend_statistics.best_versus_season
        previous_season = player.legend_statistics.previous_versus_season
        if best_season is None or previous_season is None:
            raise AttributeError
    except AttributeError:
        has_seasons = False
        best_season = Season(data={'rank': None, 'trophies': None, 'id': None})
        previous_season = Season(data={'rank': None, 'trophies': None, 'id': None})
    return [has_seasons, best_season, previous_season]


async def newly_register_account(conn: asyncpg.Connection, member_id: int, player: coc.Player) -> None:
    await conn.execute('''
                       INSERT INTO TopBuilderBasePlayers(coc_tag, coc_name, best_versus_trophies)
                       VALUES ($1, $2, $3)
                       ON CONFLICT DO NOTHING
                       ''',
                       player.tag, player.name, player.best_versus_trophies
                       )

    await conn.execute('''
                       INSERT INTO RegisteredBuilderBasePlayers(coc_tag, discord_member_id)
                       VALUES ($1, $2)
                       ''',
                       player.tag, member_id
                       )

    [has_seasons, best_season, previous_season] = get_seasons(player)
    if has_seasons:
        await conn.execute('''
                           UPDATE TopBuilderBasePlayers
                           SET best_season_id = $2, best_season_rank = $3, best_season_trophies = $4
                           WHERE coc_tag = $1
                           ''',
                           player.tag,
                           best_season.id, best_season.rank, best_season.trophies
                           )
        await conn.execute('''
                           INSERT INTO BuilderBaseFinishes
                           (coc_tag, finish_season_id, finish_rank, finish_trophies)
                           VALUES($1, $2, $3, $4)
                           ''',
                           player.tag,
                           best_season.id, best_season.rank, best_season.trophies
                           )

        await conn.execute('''
                           INSERT INTO BuilderBaseFinishes
                           (coc_tag, finish_season_id, finish_rank, finish_trophies)
                           VALUES($1, $2, $3, $4)
                           ON CONFLICT DO NOTHING
                           ''',
                           player.tag,
                           previous_season.id, previous_season.rank, previous_season.trophies
                           )

    await conn.execute('''
                       INSERT INTO BuilderBaseBoard(time, coc_tag, trophies, wins, builder_halls)
                       VALUES($2, $1, $3, $4, $5)
                       ''',
                       player.tag,
                       datetime.now(), player.versus_trophies,
                       player.versus_attack_wins, player.get_achievement('Un-Build It').value
                       )


async def has_reached_account_limit(conn: asyncpg.Connection, member_id: int) -> bool:
    record = await conn.fetchrow('SELECT COUNT(*) FROM RegisteredBuilderBasePlayers WHERE discord_member_id = $1',
                                 member_id)
    return record[0] > 19


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def link_account(self, ctx, player_tag, token, is_slash_command):
        try:
            player = await self.bot.coc.get_player(player_tag)
            success_message = f'You have successfully linked {player.name} :white_check_mark:'
        except coc.errors.NotFound:
            fail_response = f'Sorry, I could not find any player with the tag {player_tag}.'
            await respond_or_send(ctx, is_slash_command, fail_response)
            return

        async with self.bot.pool.acquire() as conn:
            if await has_reached_account_limit(conn, ctx.author.id):
                limit_response = 'Sorry, you can only link up to 20 accounts'
                await respond_or_send(ctx, is_slash_command, limit_response)
                return
            record = await conn.fetchrow('SELECT * FROM RegisteredBuilderBasePlayers WHERE coc_tag = $1', player.tag)
            if record:
                if record['discord_member_id'] == ctx.author.id:
                    await respond_or_send(ctx, is_slash_command, f'You already linked this {player.name} account.')
                    return
                if record['discord_member_id'] is None:
                    await conn.execute('''
                                       UPDATE RegisteredBuilderBasePlayers
                                       SET discord_member_id = $2
                                       WHERE coc_tag = $1
                                       ''',
                                       player.tag, ctx.author.id,
                                       )
                    await respond_or_send(ctx, is_slash_command, success_message)
                    return
                account_owner = self.bot.get_user(record['discord_member_id'])
                if not token:
                    claimed_message = f'{account_owner} already linked this account. ' \
                                      f'You can overtake it by running this command again and providing your token.' \
                                      f'You can find this token in game in the extended settings at the very bottom.'
                    await respond_or_send(ctx, is_slash_command, claimed_message)
                else:
                    if not await self.bot.coc.verify_player_token(player.tag, token):
                        wrong_token_message = f'This token is not correct, claiming {player.name} failed.'
                        await respond_or_send(ctx, is_slash_command, wrong_token_message)
                        return
                    await conn.execute('''
                                       UPDATE RegisteredBuilderBasePlayers
                                       SET discord_member_id = $2
                                       WHERE coc_tag = $1
                                       ''',
                                       player.tag, ctx.author.id,
                                       )
                    await account_owner.send(f'{ctx.author} has just claimed the following account: {player.name}.'
                                             f'You can reclaim it by using `/i-am` and provide your token.'
                                             f'You can find this token in game in the extended settings at the very bottom.')
                    await respond_or_send(ctx, is_slash_command, success_message)
                    return
            await newly_register_account(conn, ctx.author.id, player)
        await respond_or_send(ctx, is_slash_command, success_message)

    async def unlink_account(self, ctx, player_tag, is_slash_command):
        player_tag = coc.utils.correct_tag(player_tag)
        async with self.bot.pool.acquire() as conn:
            associated_tags = await conn.fetch('''
                                               SELECT coc_tag
                                               FROM RegisteredBuilderBasePlayers
                                               WHERE discord_member_id = $1
                                               ''',
                                               ctx.author.id)
            if player_tag not in [record[0] for record in associated_tags]:
                if is_slash_command:
                    await ctx.respond('You have not linked this player, so I can not unlink it.')
                else:
                    await ctx.send('You have not linked this player, so I can not unlink it.')
                return
            await conn.execute('''
                               UPDATE RegisteredBuilderBasePlayers
                               SET discord_member_id = NULL
                               WHERE coc_tag = $1
                               ''',
                               player_tag)
            if is_slash_command:
                await ctx.respond('Account unlinked :white_check_mark:')
            else:
                await ctx.send('Account unlinked :white_check_mark:')

    @commands.slash_command(name='i-am', description='Register your coc accounts in my database so I can track them')
    async def i_am(self, ctx: ApplicationContext,
                   player_tag: Option(str, name='player-tag', description='Which tag ist the one of your account'),
                   token: Option(str, 'This is optional. You only need it if someone else has already claimed your '
                                      'account.', default='')):
        await ctx.defer()
        await self.link_account(ctx, player_tag, token, True)

    @commands.slash_command(name='i-am-not', description='Unlink an account.')
    async def i_am_not(self, ctx: ApplicationContext,
                       player_tag: Option(str, name='player-tag', description='Which account do you want to unlink?')):
        await ctx.defer()
        await self.unlink_account(ctx, player_tag, True)


def setup(bot):
    bot.add_cog(Registration(bot))
