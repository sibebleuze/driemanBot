#!/usr/bin/env python3
import gc  # noqa
import os  # noqa
import random  # noqa
import sys  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

from game import Game  # noqa
from player import Player  # noqa

gc.enable()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('TEST_GUILD') if os.getenv('TESTER') == 'on' else os.getenv('WINA_GUILD')
CHANNEL = os.getenv('DRIEMAN_CHANNEL')
help_command = commands.DefaultHelpCommand(no_category="DriemanBot commando's", help='Toont dit bericht')
bot = commands.Bot(command_prefix='3man ', help_command=help_command)
bot.spel = None


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
#            "start - een nieuw spel starten als er genoeg spelers actief zijn" \
#            "rol - rol de dobbelsteen als het jouw beurt is" \
#            "opgeven - jezelf uit de lijst van actieve spelers verwijderen" \
#            "uitdelen - een aantal slokken uitdelen aan een bepaalde persoon" \
#            "tempus in - de drieman bot houdt tijdelijk voor je bij hoeveel je moet drinken" \
#            "tempus ex - de drieman bot deelt mee hoeveel je moet drinken na je pauze" \
#            "spelers - geeft een lijst terug van alle actieve spelers"
# create more commands to handle all possible 3man inputs
@bot.command(name='regels', help='De link naar de regels printen')
async def rules(ctx):
    await ctx.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")


@bot.command(name='meedoen', help='Jezelf toevoegen aan de lijst van actieve spelers')
async def join(ctx):
    if not bot.spel:
        bot.spel = Game()
        await ctx.channel.send("Er is een nieuw spel begonnen.")
    player = Player(ctx.author.name)
    bot.spel.add_player(player)
    await ctx.channel.send(f"Speler {player.name} is in het spel gekomen.")


@bot.command(name='opgeven', help='Jezelf verwijderen uit de lijst van actieve spelers')
async def quit(ctx):
    if bot.spel:
        if ctx.author.name in [player.name for player in bot.spel.players]:
            response = bot.spel.remove_player(ctx.author.name)
            if not bot.spel.players:
                response += "\nDe laatste speler heeft het spel verlaten. Het spel is nu afgelopen.\n" \
                            "Een nieuw spel kan begonnen worden als er opnieuw vier spelers zijn."
                bot.spel = None
                gc.collect()
            elif len(bot.spel.players) <= 3:
                response += "Er zijn niet genoeg spelers om verder te spelen.\n" \
                            "Wacht tot er opnieuw genoeg spelers zijn of beëindig het spel.\n" \
                            "Een nieuwe speler kan meedoen door '3man meedoen' te typen.\n" \
                            "Het spel kan beëindigd worden door '3man stop' te typen."
                bot.spel.started = False
        else:
            response = "Je zit nog niet in het spel. Je moet eerst meedoen voor je kan opgeven."
    else:
        response = "Er zit nog helemaal niemand in het spel. \n" \
                   "Wat voor dwaze dingen probeer jij uit te halen?"
    await ctx.channel.send(response)


@bot.command(name='stop', help='Stop het spel als er minder dan 3 actieve spelers zijn')
async def stop(ctx):
    if bot.spel:
        if len(bot.spel.players) <= 3:
            response = "Het spel is nu afgelopen.\n" \
                       "Een nieuw spel kan begonnen worden als er opnieuw vier spelers zijn."
            bot.spel = None
            gc.collect()
        else:
            response = "Er zijn nog meer dan vier spelers in het spel." \
                       "Om te zorgen dat niet zomaar iedereen een actief spel kan afbreken,\n" \
                       "kan het commando '3man stop' pas gebruikt worden als er 3 spelers of minder overblijven.\n" \
                       f"Als je echt wil stoppen, zal/zullen nog {len(bot.spel.players) - 3} speler(s) het moeten opgeven."
    else:
        response = "Er is geen spel bezig. Probeer je met mijn voeten te spelen?"
    await ctx.channel.send(response)


@bot.command(name='start', help='Start het spel, werkt enkel als er voldoende spelers zijn')
async def start(ctx):
    if bot.spel:
        response = bot.spel.start_game()
    else:
        response = "Er zijn nog geen spelers. Je hebt vier spelers nodig om te kunnen beginnen (zie art. 1)."
    await ctx.channel.send(response)


@bot.command(name='spelers', help='Geeft een lijst van alle actieve spelers')
async def who_is_here(ctx):
    if bot.spel:
        response = "\n".join([f"Speler {i}: " + player.name + "" for i, player in enumerate(bot.spel.players)])
    else:
        response = "Er zijn nog geen spelers."
    await ctx.channel.send(response)


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
                       'Misschien heb je niet de juiste rechten of zit je per ongeluk in het verkeerde kanaal.\n'
                       f'De DriemanBot kan enkel gebruikt worden in het kanaal {CHANNEL}.')
    else:
        with open('err.log', 'a') as f:
            f.write(str(sys.exc_info()))


bot.run(TOKEN)
