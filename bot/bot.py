#!/usr/bin/env python3
import gc  # noqa
import os  # noqa
import sys  # noqa
import traceback  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

from gameplay.game import Game  # noqa
from gameplay.player import Player  # noqa

gc.enable()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER = os.getenv('TEST_SERVER') if os.getenv('TESTER') == 'on' else os.getenv('WINA_SERVER')
CHANNEL = os.getenv('DRIEMAN_CHANNEL')
CATEGORY = os.getenv('DRIEMAN_CATEGORY')
MIN_PLAYERS = int(os.getenv('MIN_TESTERS')) if os.getenv('TESTER') == 'on' else int(os.getenv('MIN_PLAYERS'))
PREFIX = os.getenv('PREFIX')
MEEDOEN, REGELS, ROL, SPELERS, START, TEMPUS, STOP, WEGGAAN, UITDELEN = os.getenv('MEEDOEN'), os.getenv(
    'REGELS'), os.getenv('ROL'), os.getenv('SPELERS'), os.getenv('START'), os.getenv('TEMPUS'), os.getenv(
    'STOP'), os.getenv('WEGGAAN'), os.getenv('UITDELEN')


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = options.pop('no_category', "DriemanBot commando's")
        self.command_attrs = attrs = options.pop('command_attrs', {})
        attrs.setdefault('name', 'help')
        attrs.setdefault('help', 'Toon dit bericht')

    def get_ending_note(self):
        """:class:`str`: Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Typ {0}{1} commando voor meer info over een commando.\n".format(self.clean_prefix, command_name)


help_command = CustomHelpCommand()
bot = commands.Bot(command_prefix=PREFIX, help_command=help_command)
bot.spel = None


@bot.check
async def in_drieman_channel(ctx):
    if not (ctx.channel.name == CHANNEL and ctx.channel.category.name == CATEGORY):
        raise commands.CheckFailure(message="wrong channel or category")
    return True


async def game_busy(ctx):
    if not (bot.spel is not None and isinstance(bot.spel, Game)):
        raise commands.CheckFailure(message="no active game")
    return True


@commands.check(game_busy)
async def game_not_started(ctx):
    if bot.spel.started:
        raise commands.CheckFailure(message="game already started")
    return True


@commands.check(game_busy)
async def game_started(ctx):
    if not bot.spel.started:
        raise commands.CheckFailure(message="game not started")
    return True


@commands.check(game_busy)
async def player_exists(ctx):
    if ctx.author.name not in [player.name for player in bot.spel.players]:
        raise commands.CheckFailure(message="player doesn't exist")
    return True


@commands.check(game_busy)
@commands.check(game_started)
async def not_your_turn(ctx):
    if ctx.author.name != bot.spel.beurt.name:
        raise commands.CheckFailure(message="not your turn")
    if not all([bot.spel.check_player_distributor(player.name, 0, zero_allowed=True) for player in bot.spel.players]):
        raise commands.CheckFailure("too many drink units left")
    return True


@bot.event
async def on_ready():  # the output here is only visible at server level and not in Discord
    print(f'{bot.user.name} has connected to Discord!')
    server = discord.utils.get(bot.guilds, name=SERVER)
    print(
        f'{bot.user.name} is connected to the following server:\n'
        f'{server.name} (id: {server.id})'
    )
    channel = discord.utils.get(server.channels, name=CHANNEL)
    print(f'{bot.user.name} is limited to the channel:\n'
          f'{channel.name} (id: {channel.id})')
    members = '\n - '.join([member.name for member in server.members])
    print(f'Visible Server Members:\n - {members}')


@bot.command(name=REGELS, help='De link naar de regels printen')
async def rules(ctx):
    await ctx.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")


@bot.command(name=MEEDOEN, help='Jezelf toevoegen aan de lijst van actieve spelers')
async def join(ctx):
    response = ""
    if not bot.spel:
        bot.spel = Game()
        response += "Er is een nieuw spel begonnen.\n"
    player = Player(ctx.author.name)
    bot.spel.add_player(player)
    response += f"Speler {player.name} is in het spel gekomen."
    await ctx.channel.send(response)


@bot.command(name=WEGGAAN, help='Jezelf verwijderen uit de lijst van actieve spelers')
@commands.check(game_busy)
@commands.check(player_exists)
async def leave(ctx):
    response = bot.spel.remove_player(ctx.author.name)
    if not bot.spel.players:
        response += "\nDe laatste speler heeft het spel verlaten. Het spel is nu afgelopen.\n" \
                    f"Een nieuw spel kan begonnen worden als er opnieuw {MIN_PLAYERS} spelers zijn."
        bot.spel = None
        gc.collect()
    elif len(bot.spel.players) <= (MIN_PLAYERS - 1):
        response += "\nEr zijn niet genoeg spelers om verder te spelen.\n" \
                    "Wacht tot er opnieuw genoeg spelers zijn of beëindig het spel.\n" \
                    f"Een nieuwe speler kan meedoen door '{PREFIX}{MEEDOEN}' te typen.\n" \
                    f"Het spel kan beëindigd worden door '{PREFIX}{STOP}' te typen."
        bot.spel.started = False
    await ctx.channel.send(response)


@bot.command(name=STOP, help=f'Stop het spel als er minder dan {MIN_PLAYERS} actieve spelers zijn')
@commands.check(game_busy)
async def stop(ctx):
    if len(bot.spel.players) < MIN_PLAYERS:
        response = "Het spel is nu afgelopen.\n" \
                   f"Een nieuw spel kan begonnen worden als er opnieuw {MIN_PLAYERS} spelers zijn."
        bot.spel = None
        gc.collect()
    else:
        response = f"Er zijn nog meer dan {MIN_PLAYERS - 1} spelers in het spel." \
                   "Om te zorgen dat niet zomaar iedereen een actief spel kan afbreken,\n" \
                   f"kan het commando '{PREFIX}{STOP}' pas gebruikt worden " \
                   f"als er minder dan {MIN_PLAYERS} overblijven.\n" \
                   "Als je echt wil stoppen, " \
                   f"zal/zullen nog {len(bot.spel.players) - (MIN_PLAYERS - 1)} speler(s) het spel moeten verlaten."
    await ctx.channel.send(response)


@bot.command(name=START, help='Start het spel, werkt enkel als er voldoende spelers zijn')
@commands.check(game_busy)
@commands.check(game_not_started)
async def start(ctx):
    response = bot.spel.start_game()
    await ctx.channel.send(response)


@bot.command(name=SPELERS, help='Geeft een lijst van alle actieve spelers')
@commands.check(game_busy)
async def who_is_here(ctx):
    response = "Speler:naam:te drinken eenheden:uit te delen eenheden"
    for i, player in enumerate(bot.spel.players):
        response += f"\n{i}:{player.name}:{player.achterstand}:{player.uitdelen}"
    await ctx.channel.send(response)


@bot.command(name=ROL, help='Rol de dobbelsteen als het jouw beurt is')
@commands.check(game_busy)
@commands.check(game_started)
@commands.check(not_your_turn)
async def roll(ctx):
    response = bot.spel.roll(ctx.author.name)
    await ctx.send(response)


@bot.command(name=TEMPUS, help="DriemanBot houdt tijdelijk bij hoeveel je moet drinken "
                               "en deelt je dit mee aan het einde van je tempus.\n"
                               f"Gebruik '{PREFIX}{TEMPUS} in' om je tempus te beginnen en "
                               f"'{PREFIX}{TEMPUS} ex' om je tempus te eindigen en je achterstand te weten te komen.")
@commands.check(game_busy)
@commands.check(player_exists)
async def tempus(ctx, status: str):
    if not bot.spel.check_player_distributor(ctx.author.name, 0, zero_allowed=True):
        raise commands.CheckFailure("too many drink units left")
    if status not in ["in", "ex"]:
        raise commands.CheckFailure(message="wrong tempus status")
    response = bot.spel.player_tempus(ctx.author.name, status)
    await ctx.channel.send(response)


@bot.command(name=UITDELEN, help="Zeg aan wie je drankeenheden wilt uitdelen en hoeveel.\n"
                                 f"Gebruik hiervoor het format '{PREFIX}{UITDELEN} speler1:drankhoeveelheid1 "
                                 f"speler2:drankhoeveelheid2 speler3:drankhoeveelheid3' enz. "
                                 "Hierbij zijn zowel speler als drankhoeveelheid een positief geheel getal.\n"
                                 f"Om te zien welke speler welk getal heeft, kan je '{PREFIX}{SPELERS}' gebruiken.")
@commands.check(game_busy)
@commands.check(player_exists)
@commands.check(game_started)
async def distribute(ctx, *, to_distribute):
    to_distribute = [x.split(":") for x in to_distribute.split(" ")]
    try:
        to_distribute = [(int(x), int(y)) for x, y in to_distribute]
    except Exception:
        raise commands.CheckFailure(message="wrong distribute call")
    if not all([[units > 0 for _, units in to_distribute]]):
        raise commands.CheckFailure(message="wrong distribute call")
    all_units = sum([units for _, units in to_distribute])
    if not bot.spel.check_player_distributor(ctx.author.name, all_units, zero_allowed=False):
        raise commands.CheckFailure(message="not enough drink units left")
    if all([player in range(len(bot.spel.players)) for player in [p for p, _ in to_distribute]]):
        for player, units in to_distribute:
            bot.spel.distributor(ctx.author.name, player, units)
        response = bot.spel.drink()
    else:
        response = "Een van de spelers die je probeert drank te geven bestaat niet. " \
                   f"Er zijn maar {len(bot.spel.players)} spelers. Probeer opnieuw."
    await ctx.channel.send(response)


@bot.event
async def on_error(error, *args, **kwargs):
    with open('err.txt', 'a') as f:
        f.write(str(error) + "\n" + str(sys.exc_info()) + "\n\n")
    server = discord.utils.get(bot.guilds, name=SERVER)
    channel = discord.utils.get(server.channels, name=CHANNEL)
    await channel.send("Er is een fout opgetreden. Contacteer de eigenaar van de DriemanBot.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        if str(error) == "wrong channel or category":
            await ctx.send(f'De DriemanBot kan enkel gebruikt worden in het kanaal {CHANNEL} onder {CATEGORY}.\n'
                           f'Je bevindt je nu in het kanaal {ctx.channel.name} onder {ctx.channel.category.name}.')
        elif str(error) == "no active game":
            await ctx.send(f"Er is geen spel bezig. Gebruik '{PREFIX}{MEEDOEN}' om als eerste mee te doen "
                           "of ga met iemand anders zijn voeten spelen.")
        elif str(error) == "game already started":
            await ctx.send(f"Het spel is al begonnen. "
                           f"Als je een nieuw spel wil beginnen, gebruik dan eerst '{PREFIX}{STOP}'.")
        elif str(error) == "player doesn't exist":
            await ctx.send(f"Je speelt nog niet mee met dit spel. Gebruik '{PREFIX}{MEEDOEN}' om mee te doen.\n"
                           f"Daarna kan je dit commando pas gebruiken.")
        elif str(error) == "wrong tempus status":
            await ctx.send(f"Je kan enkel '{PREFIX}{TEMPUS} in' of '{PREFIX}{TEMPUS} ex' gebruiken."
                           f"'{ctx.message.content}' is geen geldig tempus commando.")
        elif str(error) == "not your turn":
            await ctx.send("Je bent nu niet aan de beurt, wacht alsjeblieft geduldig je beurt af.\n"
                           f"Het is nu de beurt aan {bot.spel.beurt.name}")
        elif str(error) == "game not started":
            await ctx.send(f"Het spel is nog niet gestart. Gebruik eerst '{PREFIX}{START}' om het spel te starten.")
        elif str(error) == "not enough drink units left":
            await ctx.send("Je hebt niet genoeg drankeenheden meer over om uit te delen.")
        elif str(error) == "too many drink units left":
            await ctx.send("Er zijn nog drankeenheden over om uitgedeeld te worden. "
                           "Deze moeten eerst uitgedeeld worden voor er kan worden verdergespeeld. "
                           f"Gebruik '{PREFIX}{UITDELEN}' (met de juiste format) om drankeenheden uit te delen en "
                           f"herhaal daarna je gewenste commando.")
        elif str(error) == "wrong distribute call":
            await ctx.send("Gebruik het juiste format om drankeenheden uit te delen, anders lukt het niet.")
        else:
            with open('err.txt', 'a') as f:
                f.write(str(error) + "\n" + str(sys.exc_info()) + "\n\n")
            await ctx.send(
                f"Het commando '{ctx.message.content}' is gefaald. Contacteer de eigenaar van de DriemanBot.")
    elif isinstance(error, commands.errors.CommandNotFound):
        with open('err.txt', 'a') as f:
            f.write(str(error) + "\n" + str(sys.exc_info()) + "\n\n")
        await ctx.send(f"Het commando '{ctx.message.content}' is onbekend. "
                       "Contacteer de eigenaar van de DriemanBot als je denkt dat dit zou moeten werken.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        response = f"Het commando '{ctx.message.content}' heeft een verplicht argument dat hier ontbreekt."
        if ctx.message.content[:len(PREFIX) + len(UITDELEN)] == PREFIX + UITDELEN:
            response += "\nGebruik het juiste format om drankeenheden uit te delen, anders lukt het niet."
        elif ctx.message.content[:len(PREFIX) + len(TEMPUS)] == PREFIX + TEMPUS:
            response += f"\n'{ctx.message.content}' is geen geldig tempus commando."
        await ctx.send(response)
    else:
        with open('err.txt', 'a') as f:
            f.write(f"{str(ctx.message.created_at)}  {ctx.message.guild}  {ctx.message.channel.category}  "
                    f"{ctx.message.channel}  {ctx.message.author}  {ctx.message.content}\n"
                    f"{ctx.message.jump_url}\n{str(error)}\n")
            traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
            f.write("\n\n\n\n\n")
        await ctx.send(
            f"Het commando '{ctx.message.content}' is zwaar gefaald. Contacteer de eigenaar van de DriemanBot.")


bot.run(TOKEN)  # TODO: test de DriemanBot met een aantal echte spelers
