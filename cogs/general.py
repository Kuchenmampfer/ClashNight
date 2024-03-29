import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='Read some general information about me')
    async def info(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        description = 'This bot has its roots in the beginning of 2021, when my developer took a look into making ' \
                      'a discord bot in order to spam and climb the mee6 leaderboard in his server. But soon he ' \
                      'discovered that this was not possible and learned how to use the coc api and relational ' \
                      'databases instead. The bot grew, and in march 2022, it was finally ready to be released to ' \
                      'the public. Now everyone can see live in game leaderboards, ' \
                      'track their trophy pushing progress and more...\n\n' \
                      'To view my commands, use `/commands`. ' \
                      'If you like me, feel free to [invite me](https://discord.com/api/oauth2/authorize?client_id=' \
                      '854473040669966397&permissions=313344&scope=bot%20applications.commands) ' \
                      'to all your servers. If you need help, ' \
                      'have found a bug, want to request a feature or stay up to date with the my development, join my ' \
                      '[support server](https://discord.gg/qtphfZ9XFH). ' \
                      'If you want to check out my source code, do so on [github](https://github.com/Kuchenmampfer/ClashNight).'
        embed = discord.Embed(colour=discord.Colour.blue(), title='General Information about me',
                              description=description)
        async with self.bot.pool.acquire() as conn:
            guilds = await conn.fetchrow('SELECT COUNT(*) FROM DiscordGuilds')
            members = await conn.fetchrow('SELECT COUNT(*) FROM DiscordMembers '
                                          'WHERE member_id IN (SELECT r.member_id FROM GuildMemberReferences r)')
            accounts = await conn.fetchrow('SELECT COUNT(*) FROM RegisteredBuilderBasePlayers '
                                           'WHERE discord_member_id IS NOT NULL')
            embed.add_field(name='Servers', value=len(self.bot.guilds))
            embed.add_field(name='Users', value=len(self.bot.users))
            embed.add_field(name='Accounts tracked', value=accounts[0])
            support_server = self.bot.get_guild(949752401978589314)
            if support_server is not None:
                embed.set_thumbnail(url=support_server.icon.url)
            invite_button = discord.ui.Button(style=discord.ButtonStyle.link,
                                              label='invite me',
                                              url='https://discord.com/api/oauth2/authorize?client_id='
                                                  '854473040669966397&permissions=313344&scope=bot%20applications.commands')
            support_button = discord.ui.Button(style=discord.ButtonStyle.link,
                                               label='support server', url='https://discord.gg/qtphfZ9XFH')
            github_button = discord.ui.Button(style=discord.ButtonStyle.link,
                                              label='code on github', url='https://github.com/Kuchenmampfer/ClashNight')
            view = discord.ui.View(invite_button, support_button, github_button)
            await ctx.respond(embed=embed, view=view)

    @commands.slash_command(name='commands', description='Shows all my commands')
    async def show_commands(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        embed = discord.Embed(colour=discord.Colour.blue(), title='My Commands')
        global_cmd_list = await self.bot.http.get_global_commands(self.bot.application_id)
        guild_cmd_list = await self.bot.http.get_guild_commands(self.bot.application_id, ctx.guild_id)
        for cmd in sorted(global_cmd_list + guild_cmd_list, key=lambda x: x['name']):
            if cmd["description"] != '':
                try:
                    options = cmd['options']
                except KeyError:
                    embed.add_field(name=f"/{cmd['name']}", value=cmd['description'], inline=False)
                    continue
                if all([option['type'] > 2 for option in options]):
                    embed.add_field(name=f"/{cmd['name']}", value=cmd['description'], inline=False)
                else:
                    for option in sorted(options, key=lambda x: x['name']):
                        if option['type'] <= 2:
                            embed.add_field(name=f"/{cmd['name']} {option['name']}", value=option['description'],
                                            inline=False)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
