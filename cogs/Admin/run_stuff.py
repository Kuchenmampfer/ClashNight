import discord
from aioconsole import aexec
from discord import Option
from discord.ext import commands
from prettytable import PrettyTable


class RunStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild.id in [805155951324692571, 949752401978589314] and ctx.author.id == 471752948200898561

    @commands.is_owner()
    @commands.slash_command(name='eval', description='Run some code',
                            guild_ids=[805155951324692571, 949752401978589314])
    async def eval(self, ctx: discord.ApplicationContext,
                   code: Option(str, "What shall I run?")):
        await ctx.defer()
        try:
            await aexec(code + "\nawait ctx.respond(response)", {"bot": self.bot, "ctx": ctx})
        except BaseException as e:
            await ctx.respond(str(e))

    @commands.is_owner()
    @commands.slash_command(name='sql-fetch', description='Fetch some data',
                            guild_ids=[805155951324692571, 949752401978589314])
    async def sql_fetch(self, ctx: discord.ApplicationContext,
                        query: Option(str, "What shall I fetch?")):
        await ctx.defer()
        async with self.bot.pool.acquire() as conn:
            try:
                records = await conn.fetch(query)
                table = PrettyTable()
                table.field_names = [key for key in records[0].keys()]
                table.add_rows(records)
                table_str = table.get_string()
                with open('table.txt', 'w', encoding='utf-8') as f:
                    f.write(table_str)
                await ctx.respond(file=discord.File('table.txt'))
            except BaseException as e:
                await ctx.respond(str(e))


def setup(bot):
    bot.add_cog(RunStuff(bot))
