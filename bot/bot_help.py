#!/usr/bin/env python3
import discord  # noqa
from discord.ext import commands  # noqa


class CustomHelpCommand(commands.DefaultHelpCommand):  # define a custom help command, mostly to put some stuff in Dutch
    def __init__(self, **options):
        options['verify_checks'] = False  # don't hide commands in the help overview when checks don't return True
        options['command_attrs'] = options.get('command_attrs', {})
        options['command_attrs'].setdefault('name', 'help')
        options['command_attrs'].setdefault('help', 'Toon dit bericht')  # above three lines to set this Dutch string
        super().__init__(**options)  # all other init values inherited from DefaultHelpCommand

    def get_ending_note(self):  # put this return string in Dutch
        command_name = self.invoked_with
        return "Typ {0}{1} commando voor meer info over een commando.\n".format(self.clean_prefix, command_name)

    def command_not_found(self, string):  # put this return string in Dutch
        return f"De DriemanBot heeft geen commando '{string}'."
