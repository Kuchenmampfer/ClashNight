import coc
import discord
from aioconsole import aexec
from discord.ext import commands
from prettytable import PrettyTable


class RunStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild.id == 805155951324692571 and ctx.author.id == 471752948200898561

    @commands.is_owner()
    @commands.command(name='eval')
    async def eval(self, ctx, *, code: str):
        try:
            await aexec(code + "\nawait ctx.send(response)", {"bot": self.bot, "ctx": ctx})
        except BaseException as e:
            await ctx.send(e)

    @commands.command(name='sql_fetch')
    async def sql_fetch(self, ctx, *, sql_query):
        async with self.bot.pool.acquire() as conn:
            try:
                records = await conn.fetch(sql_query)
                table = PrettyTable()
                table.field_names = [key for key in records[0].keys()]
                table.add_rows(records)
                table_str = table.get_string()
                with open('table.txt', 'w', encoding='utf-8') as f:
                    f.write(table_str)
                await ctx.send(file=discord.File('table.txt'))
            except BaseException as e:
                await ctx.send(e)

    @commands.command(name='reload')
    async def reload(self, ctx, cog):
        name = 'cogs.' + cog
        try:
            self.bot.reload_extension(name)
            await ctx.send(f'`{cog}` wurde neu geladen :white_check_mark:')
        except commands.ExtensionError as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(RunStuff(bot))
