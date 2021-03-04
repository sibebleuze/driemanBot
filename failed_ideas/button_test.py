# Minimum working example of the bot reacting to button presses by the user
# Can be used to help people type less
# I used this example to test some stuff out, the current version of this file will fail to run

import discord
from discord.ext import commands
from discord.ext import buttons
from dotenv import load_dotenv
import os
import gameplay.constants as const  # noqa

load_dotenv()  # load the Discord token as environment variable
TOKEN = os.getenv('DISCORD_TOKEN')


class MyPaginator(buttons.Paginator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @buttons.button(emoji=b'1\xef\xb8\x8f\xe2\x83\xa3'.decode('utf-8'), try_remove=False)
    async def record_button(self, ctx, member):
        for comm in ctx.bot.commands:
            if comm.name == 'oproep':
                if all([await check(ctx) for check in comm.checks]):
                    await comm(ctx)

    # @buttons.button(emoji=b'\x32'.decode('utf-8'), try_remove=False)
    # async def silly_button(self, ctx, member):
    #     await ctx.channel.send('Beep boop...')

    @buttons.button(emoji=const.CLINKING_BEERS, try_remove=False)
    async def distributor(self, ctx, member):
        def checkforreaction(reaction, user):
            return user == ctx.author and str(reaction.emoji) in const.EMOJIS

        await ctx.channel.send("Kies iemand om aan uit te delen.")
        responses = await ctx.channel.history(limit=1).flatten()
        for i in range(1, 31):
            await responses[0].add_reaction(emoji=const.NUMBERS[i])
        reaction, user = await self.client.wait_for('reaction_add', timeout=None, check=checkforreaction)
        player_number = const.EMOJIS[reaction]
        await ctx.channel.send("Kies een hoeveelheid om uit te delen.")
        response = await ctx.channel.history(limit=1).flatten()[0]
        for i in range(1, 11):
            response.add_reaction(emoji=const.NUMBERS[i])
        reaction, user = await self.client.wait_for('reaction_add', timeout=None, check=checkforreaction)
        amount = const.EMOJIS[reaction]
        print(f'3man uitdelen {player_number}:{amount}')


bot = commands.Bot(command_prefix='??')


@bot.command()
async def test(ctx):
    pagey = MyPaginator(title='Silly Paginator', colour=0xc67862, embed=False, timeout=99999, use_defaults=False,
                        entries=[1, 2, 3], length=3, format='**')

    await pagey.start(ctx)


async def is_correct_server(ctx):
    SERVER = const.TEST_SERVER if const.TESTER else const.USER_SERVER
    return True


@bot.command()
@commands.check(is_correct_server)
async def oproep(ctx):
    await ctx.channel.send("Oproep ontvangen.")


@bot.event
async def on_ready():
    messages = await bot.guilds[1].channels[2].history(limit=1).flatten()
    message = messages[0]
    print('Ready!')


bot.run(TOKEN)
