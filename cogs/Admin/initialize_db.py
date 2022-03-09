import asyncio

from discord.ext import commands


class InitializeDatabase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild.id == 805155951324692571

    @commands.command(name='initialize_db')
    async def init_db(self, ctx):
        async with self.bot.pool.acquire() as conn:

            await conn.execute('''
                        CREATE TABLE IF NOT EXISTS DiscordGuilds
                        (
                        guild_id BIGINT PRIMARY KEY,
                        guild_name VARCHAR(100),
                        bot_prefix CHARACTER(1) DEFAULT '!',
                        interaction_channel_id BIGINT,
                        leaderboard_channel_id BIGINT,
                        base_channel_id BIGINT,
                        default_loc_id INTEGER
                        );
                        
                        CREATE TABLE IF NOT EXISTS DiscordMembers
                        (
                        member_id BIGINT PRIMARY KEY,
                        member_name VARCHAR(32) NOT NULL,
                        base_count SMALLINT DEFAULT 0,
                        vier_gewinnt_score SMALLINT DEFAULT 0,
                        vier_gewinnt_elo SMALLINT DEFAULT 100,
                        music_quiz_score SMALLINT DEFAULT 0
                        );
                        
                        CREATE TABLE IF NOT EXISTS GuildMemberReferences
                        (
                        guild_id BIGINT NOT NULL,
                        member_id BIGINT NOT NULL,
                        CONSTRAINT fk_guild
                            FOREIGN KEY(guild_id)
                                REFERENCES DiscordGuilds(guild_id)
                                ON DELETE CASCADE,
                        CONSTRAINT fk_member
                            FOREIGN KEY(member_id)
                                REFERENCES DiscordMembers(member_id)
                                ON DELETE CASCADE
                        );
                        
                        CREATE TABLE IF NOT EXISTS GuildTextCommands
                        (
                        command_name VARCHAR(32) NOT NULL,
                        command_return_text TEXT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        is_public BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY(command_name, guild_id),
                        CONSTRAINT fk_guild
                            FOREIGN KEY(guild_id)
                                REFERENCES DiscordGuilds(guild_id)
                                ON DELETE CASCADE
                        );
                        
                        CREATE TABLE IF NOT EXISTS TopBuilderBasePlayers
                        (
                        coc_tag VARCHAR(12) PRIMARY KEY,
                        coc_name VARCHAR(16) NOT NULL,
                        best_versus_trophies SMALLINT,
                        best_season_id CHAR(7),
                        best_season_rank INTEGER,
                        best_season_trophies SMALLINT
                        );
                        
                        CREATE TABLE IF NOT EXISTS RegisteredBuilderBasePlayers
                        (
                        coc_tag VARCHAR(12) PRIMARY KEY,
                        discord_member_id BIGINT,
                        best_finish_place INTEGER,
                        best_finish_trophies SMALLINT,
                        legend_cups INTEGER,
                        bb_elo SMALLINT DEFAULT 100,
                        CONSTRAINT fk_bb_player
                            FOREIGN KEY(coc_tag)
                                REFERENCES TopBuilderBasePlayers(coc_tag)
                                ON DELETE CASCADE,
                        CONSTRAINT fk_member
                            FOREIGN KEY(discord_member_id)
                                REFERENCES DiscordMembers(member_id)
                                ON DELETE CASCADE
                        );
                        
                        CREATE TABLE IF NOT EXISTS BuilderBaseBoard
                        (
                        time TIMESTAMP WITH TIME ZONE NOT NULL,
                        coc_tag VARCHAR(12) NOT NULL,
                        trophies SMALLINT,
                        wins SMALLINT,
                        builder_halls SMALLINT,
                        is_season_end BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY(time, coc_tag),
                        CONSTRAINT fk_coc_bb_player
                            FOREIGN KEY(coc_tag)
                                REFERENCES RegisteredBuilderBasePlayers(coc_tag)
                                ON DELETE CASCADE
                        );
                        
                        CREATE TABLE IF NOT EXISTS BuilderBaseFinishes
                        (
                        coc_tag VARCHAR(12) NOT NULL,
                        finish_season_id CHARACTER(7) NOT NULL,
                        finish_rank INTEGER NOT NULL,
                        finish_trophies INTEGER NOT NULL,
                        PRIMARY KEY (coc_tag, finish_season_id),
                        CONSTRAINT fk_coc_bb_player
                            FOREIGN KEY(coc_tag)
                                REFERENCES RegisteredBuilderBasePlayers(coc_tag)
                                ON DELETE CASCADE
                        );
                        
                        CREATE TABLE IF NOT EXISTS BuilderBaseLeaderboards
                        (
                        record_date DATE NOT NULL,
                        region VARCHAR(16) NOT NULL,
                        tags VARCHAR(12)[200],
                        names VARCHAR(16)[200],
                        trophies SMALLINT[200],
                        is_season_end BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY(record_date, region, is_season_end)
                        );
                        
                        CREATE TABLE IF NOT EXISTS BuilderBaseTopTen
                        (
                        time TIMESTAMP WITH TIME ZONE NOT NULL,
                        region VARCHAR(16) NOT NULL,
                        tags VARCHAR(12)[10],
                        names VARCHAR(16)[10],
                        trophies SMALLINT[10],
                        PRIMARY KEY(time, region)
                        );
                        
                        CREATE TABLE IF NOT EXISTS TrophyChangeAnalysis
                        (
                        time TIMESTAMP WITH TIME ZONE NOT NULL,
                        previous_places SMALLINT[2] NOT NULL,
                        previous_trophies SMALLINT[2] NOT NULL,
                        trophy_change SMALLINT NOT NULL,
                        PRIMARY KEY(time, previous_places)
                        );
                        
                        CREATE TABLE IF NOT EXISTS TopLadderActivity
                        (
                        time TIMESTAMP WITH TIME ZONE PRIMARY KEY,
                        duels SMALLINT NOT NULL
                        );
                        
                        CREATE TABLE IF NOT EXISTS DuelGamesResults
                        (
                        time TIMESTAMP WITH TIME ZONE NOT NULL,
                        game VARCHAR(16) NOT NULL,
                        winner_id BIGINT,
                        loser_id BIGINT,
                        was_draw BOOLEAN DEFAULT FALSE,
                        CONSTRAINT fk_winner
                            FOREIGN KEY(winner_id)
                                REFERENCES DiscordMembers(member_id)
                                ON DELETE SET NULL,
                        CONSTRAINT fk_loser
                            FOREIGN KEY(loser_id)
                                REFERENCES DiscordMembers(member_id)
                                ON DELETE SET NULL
                        );
                        
                        CREATE TABLE IF NOT EXISTS MusicQuizzes
                        (
                        lb_message_id BIGINT PRIMARY KEY,
                        guild_id BIGINT NOT NULL,
                        quiz_date DATE,
                        CONSTRAINT fk_guild
                            FOREIGN KEY(guild_id)
                                REFERENCES DiscordGuilds(guild_id)
                                ON DELETE CASCADE
                        );
                           
                        CREATE TABLE IF NOT EXISTS MusicQuizScores
                        (
                        lb_message_id BIGINT NOT NULL,
                        participator_id BIGINT NOT NULL,
                        points SMALLINT NOT NULL,
                        place SMALLINT NOT NULL,
                        PRIMARY KEY(lb_message_id, participator_id),
                        CONSTRAINT fk_member
                            FOREIGN KEY(participator_id)
                                REFERENCES DiscordMembers(member_id)
                                ON DELETE CASCADE,
                        CONSTRAINT fk_quiz
                            FOREIGN KEY(lb_message_id)
                                REFERENCES MusicQuizzes(lb_message_id)
                                ON DELETE CASCADE
                        );
                        ''')
            #  IF NOT EXISTS is not possible when creating views,
            #  so I needed to exclude this from the command in order to avoid conflicts
        await ctx.send('Tables erfolgreich generiert :white_check_mark:')

    @commands.command(name='create_view')
    async def create_view(self, ctx):
        async with self.bot.pool.acquire() as conn:
            await conn.execute('''
                               CREATE VIEW FullCocPlayers AS
                                   SELECT t.coc_tag coc_tag,
                                       t.coc_name coc_name,
                                       t.best_versus_trophies best_versus_trophies,
                                       t.best_season_id best_season_id,
                                       t.best_season_rank best_season_rank,
                                       t.best_season_trophies best_season_trophies,
                                       r.legend_cups legend_cups,
                                       b.trophies trophies, b.wins wins, b.builder_halls builder_halls
                                   FROM BuilderBaseBoard b
                                   JOIN RegisteredBuilderBasePlayers r
                                       ON r.coc_tag = b.coc_tag
                                   JOIN TopBuilderBasePlayers t
                                       ON t.coc_tag = b.coc_tag
                                   WHERE b.time = (SELECT MAX(time) FROM BuilderBaseBoard b1
                                       WHERE b1.coc_tag = b.coc_tag)
                               ''')
        await ctx.send('View created :white_check_mark:')


def setup(bot):
    bot.add_cog(InitializeDatabase(bot))
