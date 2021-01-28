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
    bot.shutdown = shutdown


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
    shutdown = bot.shutdown
