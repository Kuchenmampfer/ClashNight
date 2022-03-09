import discord
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guild_log_channel = await self.bot.fetch_channel(951240760399921212)
        embed = discord.Embed(colour=discord.Colour.blue(),
                              description=f'Joined server `{guild.name:32}` with `{guild.member_count:6} members.')
        await guild_log_channel.send(embed=embed)
        async with self.bot.pool.acquire() as conn:
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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.pool.acquire() as conn:
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
                                   member.guild.id, member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with self.bot.pool.acquire() as conn:
            if not member.bot:
                await conn.execute('''
                                   DELETE FROM GuildMemberReferences
                                   WHERE guild_id = $1 AND member_id = $2
                                   ''',
                                   member.guild.id, member.id)


def setup(bot):
    bot.add_cog(Events(bot))
