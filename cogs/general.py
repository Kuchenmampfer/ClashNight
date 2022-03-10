import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(guild_ids=[805155951324692571], description='Read some general information about me')
    async def info(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        description = 'This bot has its roots in the beginning of 2021, when my developer took a look into making ' \
                      'a discord bot in order to spam and climb the mee6 leaderboard in his server. But soon he ' \
                      'discovered that this was not possible and learned how to use the coc api and relational ' \
                      'databases instead. The bot grew, and in march 2022, it was finally ready to be released to ' \
                      'the public. Now everyone can see live in game leaderboards, ' \
                      'track their trophy pushing progress and more...\n\n' \
                      'If you like me, feel free to [invite me](https://discord.com/api/oauth2/authorize?client_id=8544730' \
                      '40669966397&permissions=378880&scope=bot%20applications.commands) to all your servers. If you need help, ' \
                      'have found a bug, want to request a feature or stay up to date with the my development, join my ' \
                      '[support server](https://discord.gg/qtphfZ9XFH). ' \
                      'If you want to check out my source code, do so on [github](github_link).'
        embed = discord.Embed(colour=discord.Colour.blue(), title='General Information about me',
                              description=description)
        async with self.bot.pool.acquire() as conn:
            guilds = await conn.fetchrow('SELECT COUNT(*) FROM DiscordGuilds')
            members = await conn.fetchrow('SELECT COUNT(*) FROM DiscordMembers')
            accounts = await conn.fetchrow('SELECT COUNT(*) FROM RegisteredBuilderBasePlayers '
                                           'WHERE discord_member_id IS NOT NULL')
            embed.add_field(name='Servers', value=guilds[0])
            embed.add_field(name='Users', value=members[0])
            embed.add_field(name='Accounts tracked', value=accounts[0])
            support_server = self.bot.get_guild(949752401978589314)
            if support_server is not None:
                embed.set_thumbnail(url=support_server.icon.url)
            invite_button = discord.ui.Button(style=discord.ButtonStyle.link,
                                              label='invite me', url='https://discord.com/api/oauth2/authorize?'
                                                                     'client_id=854473040669966397&permissions=378880&'
                                                                     'scope=bot%20applications.commands')
            support_button = discord.ui.Button(style=discord.ButtonStyle.link,
                                               label='support server', url='https://discord.gg/qtphfZ9XFH')
            view = discord.ui.View(invite_button, support_button)
            await ctx.respond(embed=embed, view=view)

    @commands.slash_command(guild_ids=[805155951324692571], name='commands', description='Shows all my commands')
    async def show_commands(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        embed = discord.Embed(colour=discord.Colour.blue(), title='My Commands')
        for cmd in await self.bot.http.get_global_commands(self.bot.application_id):
            embed.add_field(name=cmd['name'], value=f'*{cmd["description"]}*', inline=False)
        for cmd in await self.bot.http.get_guild_commands(self.bot.application_id, ctx.guild_id):
            embed.add_field(name=cmd['name'], value=f'*{cmd["description"]}*', inline=False)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
