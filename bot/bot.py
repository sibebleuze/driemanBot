#!/usr/bin/env python3
import gc  # noqa
import importlib  # noqa
import os  # noqa
import sys  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

import bot_help  # noqa
import gameplay.constants as const  # noqa
import gameplay.game  # noqa
import gameplay.player  # noqa

gc.enable()  # explicitly enable garbage collector
load_dotenv()  # load the Discord token as environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
# use different values when testing vs. when actually in use,
CHANNEL = const.TEST_CHANNEL if const.TESTER else const.DRIEMAN_CHANNEL  # these values all together determine channel
CATEGORY = const.TEST_CATEGORY if const.TESTER else const.DRIEMAN_CATEGORY  # and category, by unique IDs

shutdown = False
while not shutdown:
    # reload some imports in every new loop, so we can use this to update code while running
    importlib.reload(sys.modules["gameplay.constants"])
    importlib.reload(sys.modules["gameplay.player"])
    importlib.reload(sys.modules["gameplay.game"])
    importlib.reload(sys.modules["bot_help"])
    import gameplay.constants as const  # noqa

    CHANNEL = const.TEST_CHANNEL if const.TESTER else const.DRIEMAN_CHANNEL
    CATEGORY = const.TEST_CATEGORY if const.TESTER else const.DRIEMAN_CATEGORY

    help_command = bot_help.CustomHelpCommand()  # initialize the custom help command
    bot = commands.Bot(command_prefix=const.PREFIX, help_command=help_command)  # initialize the bot
    bot.load_extension('bot_commands')  # load all commands from bot_commands.py
    bot.help_command.cog = bot.cogs["DriemanBot commando's"]  # give help command the same help category as the others


    @bot.check  # global check for all commands
    async def in_drieman_channel(ctx):  # check if command message is in correct channel and category
        if not (ctx.channel.id == CHANNEL and ctx.channel.category.id == CATEGORY):
            raise commands.CheckFailure(message="wrong channel or category")
        return True


    @bot.check  # global check for all commands
    async def oneliner(ctx):  # check if command message consists of one line only
        if "\n" in ctx.message.content:
            raise commands.CheckFailure(message="multiline message")
        return True


    @bot.command(pass_context=True, hidden=True)
    async def power(ctx, status):  # command to shutdown or restart the bot
        global shutdown
        if ctx.author.mention == const.PROGRAMMER:  # for one person only (same one that gets all the error messages)
            if status not in ["on", "off"]:
                raise commands.errors.CommandNotFound  # mistyped, just give a command not found, easy to figure out
            else:
                await ctx.message.delete()  # hide the existence of this command a bit, since no one else can use it
                if status == "off":  # shutdown
                    shutdown = True  # will break the surrounding while loop and shut down the python script
                messages = await ctx.channel.history().flatten()
                for message in messages:
                    if message.content == "De DriemanBot staat aan." and message.author == ctx.bot.user:
                        await message.delete()
                    elif message.content == "De DriemanBot staat uit." and message.author == ctx.bot.user:
                        await message.delete()
                await ctx.channel.send("De DriemanBot staat uit.")  # message to let people know the bot is gone
                await bot.logout()  # actual shutdown
                t = bot.cogs["DriemanBot commando's"].time
                print(f"{bot.user.name} ({t}) is offline.")  # confirmation of being offline in shell
        else:
            await ctx.channel.send("Ontoereikende permissies")  # tell other people what they're doing wrong


    @bot.event  # disable default on_message,
    async def on_message(message):
        pass


    @bot.event  # on_error
    async def on_error(error, *args, **kwargs):
        pass


    @bot.event  # and on_command_error and use the ones from the cog instead
    async def on_command_error(ctx, error):
        pass


    task = bot.loop.create_task(bot.start(TOKEN))  # two lines to start the bot in such a way that the event loop ...
    bot.loop.run_until_complete(task)  # ... doesn't get closed and the restart and shutdown commands above work
