#!/usr/bin/env python3
import os  # noqa
import random  # noqa
import sys  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD') if os.getenv('TESTER') == 'on' else os.getenv('WINA_GUILD')
CHANNEL = os.getenv('DRIEMAN_CHANNEL')
bot = commands.Bot(command_prefix='3man ')


@bot.check
async def in_drieman_channel(ctx):
    return ctx.channel.name == CHANNEL


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    # guild = discord.utils.get(bot.guilds, name=GUILD)
    for guild in bot.guilds:
        print(
            f'{bot.user.name} is connected to the following server:\n'
            f'{guild.name}(id: {guild.id})'
        )
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Visible Server Members:\n - {members}')


# helpdesk = "Overzicht van de DriemanBot commando's" \
#            "=======================================" \
#            "help - deze hulp weergeven" \
#            "regels - de link naar de regels printen" \
#            "meedoen - jezelf toevoegen aan de lijst van actieve spelers" \
#            "driemannen - een nieuw spel starten als er genoeg spelers actief zijn" \
#            "rol - rol de dobbelsteen als het jouw beurt is" \
#            "opgeven - jezelf uit de lijst van actieve spelers verwijderen" \
#            "uitdelen - een aantal slokken uitdelen aan een bepaalde persoon" \
#            "tempus in - de drieman bot houdt tijdelijk voor je bij hoeveel je moet drinken" \
#            "tempus ex - de drieman bot deelt mee hoeveel je moet drinken na je pauze"

# create more commands to handle all possible 3man inputs
# meedoen: met ctx.author de naam bepalen
# regels: https://wina-gent.be/drieman.pdf

@bot.command(name='regels', help='De link naar de regels printen')
async def rules(ctx):
    await ctx.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")


@bot.command(name='rol', help='Rol de dobbelsteen als het jouw beurt is')
async def roll(ctx):
    # implementeer een manier om te checken dat deze speler aan de beurt is
    dice = [
        str(random.choice(range(1, 6 + 1)))
        for _ in range(2)
    ]
    # implementeer een functie om te bepalen voor welke spelers deze worp iets betekent
    response = ', '.join(dice)  # tijdelijke filler
    await ctx.send(response)


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        f.write(str(sys.exc_info()))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Je kan dit commando hier niet gebruiken.\n'
                       'Misschien heb je niet de juiste rechten of zit je per ongeluk in het verkeerde kanaal.')
    else:
        with open('err.log', 'a') as f:
            f.write(str(sys.exc_info()))


bot.run(TOKEN)
