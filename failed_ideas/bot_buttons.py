# i tried something with emoji buttons, but it doesn't work because i need numbers > 10 and discord doesn't have them

import discord  # noqa
from discord.ext import buttons  # noqa
from discord.ext import commands  # noqa

import gameplay.constants as const  # noqa


class AmountSelectButtons(buttons.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PlayerSelectButtons(buttons.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # for i in range(6):
    #     @buttons.button(emoji=const.NUMBERS[i], try_remove=False)
    #     async def player(self, ctx, member):
    #         amount_selector = AmountSelectButtons(player=i, entries=['Aantal drankeenheden'], embed=False,
    #                                               timeout=None, use_defaults=False)
    #         await amount_selector.start(ctx)


class DriemanButtons(buttons.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @buttons.button(emoji=const.GAME_DIE, try_remove=False)
    async def roller(self, ctx, member):
        for comm in ctx.bot.commands:
            if comm.name == const.ROL:
                if all([await check(ctx) for check in comm.checks]):
                    await comm(ctx)

    @buttons.button(emoji=const.CLINKING_BEERS, try_remove=False)
    async def distributor(self, ctx, member):
        def checkforreaction(reaction, user):
            return user == ctx.author and str(reaction.emoji) in const.EMOJIS

        ctx.channel.send("Kies iemand om aan uit te delen.")
        response = await ctx.channel.history(limit=1).flatten()[0]
        for i in range(1, 31):
            response.add_reaction(emoji=const.NUMBERS[i])
        reaction, user = await self.client.wait_for('reaction_add', timeout=None, check=checkforreaction)
        player_number = const.EMOJIS[reaction]
        ctx.channel.send("Kies een hoeveelheid om uit te delen.")
        response = await ctx.channel.history(limit=1).flatten()[0]
        for i in range(1, 11):
            response.add_reaction(emoji=const.NUMBERS[i])
        reaction, user = await self.client.wait_for('reaction_add', timeout=None, check=checkforreaction)
        amount = const.EMOJIS[reaction]
        for comm in ctx.bot.commands:
            if comm.name == const.UITDELEN:
                if all([await check(ctx) for check in comm.checks]):
                    await comm(ctx, uitgedeeld=f'{player_number}:{amount}')
