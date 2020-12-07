#!/usr/bin/env python3
import gc  # noqa
import os  # noqa
import sys  # noqa
import traceback  # noqa
from datetime import datetime  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

from gameplay.game import Game  # noqa
from gameplay.player import Player  # noqa

gc.enable()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TESTER = os.getenv('TESTER') == 'on'
SERVER = os.getenv('TEST_SERVER') if TESTER else os.getenv('WINA_SERVER')
CHANNEL = os.getenv('TEST_CHANNEL') if TESTER else os.getenv('DRIEMAN_CHANNEL')
CATEGORY = os.getenv('TEST_CATEGORY') if TESTER else os.getenv('DRIEMAN_CATEGORY')
MIN_PLAYERS = int(os.getenv('MIN_TESTERS')) if TESTER else int(os.getenv('MIN_PLAYERS'))
PREFIX = os.getenv('PREFIX')
MEEDOEN, REGELS, ROL, SPELERS, START, TEMPUS, STOP, WEGGAAN, UITDELEN, BIJNAAM = os.getenv('MEEDOEN'), os.getenv(
    'REGELS'), os.getenv('ROL'), os.getenv('SPELERS'), os.getenv('START'), os.getenv('TEMPUS'), os.getenv(
    'STOP'), os.getenv('WEGGAAN'), os.getenv('UITDELEN'), os.getenv('BIJNAAM')
DUBBELDRIEMAN = os.getenv('DUBBELDRIEMAN')


class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        options['no_category'] = "DriemanBot commando's"
        options['verify_checks'] = False
        options['command_attrs'] = options.get('command_attrs', {})
        options['command_attrs'].setdefault('name', 'help')
        options['command_attrs'].setdefault('help', 'Toon dit bericht')
        super().__init__(**options)

    def get_ending_note(self):
        command_name = self.invoked_with
        return "Typ {0}{1} commando voor meer info over een commando.\n".format(self.clean_prefix, command_name)

    def command_not_found(self, string):
        return f"De DriemanBot heeft geen commando '{string}'."


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
    if str(ctx.author) not in [player.fullname for player in bot.spel.players]:
        raise commands.CheckFailure(message="player doesn't exist")
    return True


@commands.check(game_busy)
@commands.check(game_started)
async def not_your_turn(ctx):
    if str(ctx.author) != bot.spel.beurt.fullname:
        raise commands.CheckFailure(message="not your turn")
    return True


@bot.event
async def on_ready():  # the output here is only visible at server level and not in Discord
    if TESTER:
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


@bot.command(name=REGELS, help='De link naar de regels printen.')
async def rules(ctx):
    await ctx.channel.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")


@bot.command(name=MEEDOEN, help="Jezelf toevoegen aan de lijst van actieve spelers.\n"
                                "Met het optionele argument 'bijnaam' kan je een bijnaam "
                                "bestaande uit 1 woord kiezen.")
async def join(ctx, bijnaam=None):
    response = ""
    if not bot.spel:
        bot.spel = Game()
        response += "Er is een nieuw spel begonnen.\n"
    if bijnaam is not None:
        if not (isinstance(bijnaam, str) and " " not in bijnaam and bijnaam != ""):
            raise commands.CheckFailure(message="wrong nickname input")
    player = Player(ctx.author).set_nickname(bijnaam)
    if player.fullname in [player.fullname for player in bot.spel.players]:
        raise commands.CheckFailure(message="player already exists")
    bot.spel.add_player(player)
    response += f"{player.name} ({player.nickname}) is in het spel gekomen."
    await ctx.channel.send(response)


@bot.command(name=BIJNAAM, help='Stel je bijnaam in als je dat nog niet gedaan had '
                                'of wijzig je bijnaam als je een andere wilt.')
@commands.check(game_busy)
@commands.check(player_exists)
async def nickname(ctx, *, bijnaam: str):
    if " " in bijnaam or bijnaam == "":
        raise commands.CheckFailure(message="wrong nickname input")
    player = bot.spel.players[[player.fullname for player in bot.spel.players].index(str(ctx.author))]
    player.set_nickname(bijnaam)
    await ctx.channel.send(f"{player.name} heeft nu de bijnaam {player.nickname}.")


@bot.command(name=WEGGAAN, help='Jezelf verwijderen uit de lijst van actieve spelers.')
@commands.check(game_busy)
@commands.check(player_exists)
async def leave(ctx):
    response = bot.spel.remove_player(str(ctx.author))
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


@bot.command(name=STOP, help=f'Stop het spel als er minder dan {MIN_PLAYERS} actieve spelers zijn.')
@commands.check(game_busy)
async def stop(ctx):
    response = ""
    if len(bot.spel.players) < MIN_PLAYERS:
        for player in bot.spel.players:
            response += bot.spel.remove_player(player.fullname)
        response += "\nHet spel is nu afgelopen.\n" \
                    f"Een nieuw spel kan begonnen worden als er opnieuw {MIN_PLAYERS} spelers zijn."
        bot.spel = None
        gc.collect()
    else:
        response = f"Er zijn nog meer dan {MIN_PLAYERS - 1} spelers in het spel. " \
                   "Om te zorgen dat niet zomaar iedereen een actief spel kan afbreken," \
                   f"kan het commando '{PREFIX}{STOP}' pas gebruikt worden " \
                   f"als er minder dan {MIN_PLAYERS} overblijven. " \
                   "Als je echt wil stoppen, " \
                   f"zal/zullen nog {len(bot.spel.players) - (MIN_PLAYERS - 1)} speler(s) het spel moeten verlaten."
    await ctx.channel.send(response)


@bot.command(name=START, help='Start het spel als er voldoende spelers zijn.')
@commands.check(game_busy)
@commands.check(game_not_started)
async def start(ctx):
    response = bot.spel.start_game()
    await ctx.channel.send(response)


@bot.command(name=SPELERS, help='Geeft een lijst van alle actieve spelers.')
@commands.check(game_busy)
async def who_is_here(ctx):
    embed = discord.Embed(title='Overzicht actieve spelers')
    for i, player in enumerate(bot.spel.players):
        embed.add_field(name=f'Speler: {i}',
                        value=f"Naam: {player.name}\nBijnaam: "
                              f"{player.nickname if player.nickname is not None else ''}\nTe drinken: "
                              f"{player.achterstand}\nUit te delen: {player.uitdelen}",
                        inline=True)
    response = ""
    if bot.spel.started:
        response += f"{bot.spel.beurt.name} is aan de beurt."
    if bot.spel.drieman is not None:
        response += f" {bot.spel.drieman.name} is op dit moment drieman."
    await ctx.channel.send(response, embed=embed)


@bot.command(name=ROL, help='Rol de dobbelsteen als het jouw beurt is.')
@commands.check(game_busy)
@commands.check(game_started)
@commands.check(not_your_turn)
async def roll(ctx):
    response, url = bot.spel.roll(str(ctx.author))
    if url is not None:
        file = discord.File(url)
        embed = discord.Embed()
        embed.set_image(url="attachment://" + url)
        await ctx.channel.send(response, file=file, embed=embed)
    else:
        await ctx.channel.send(response)


@bot.command(name=TEMPUS, help="DriemanBot houdt tijdelijk bij hoeveel je moet drinken "
                               "en deelt je dit mee aan het einde van je tempus. "
                               f"Gebruik '{PREFIX}{TEMPUS} in' om je tempus te beginnen en "
                               f"'{PREFIX}{TEMPUS} ex' om je tempus te eindigen en je achterstand te weten te komen.")
@commands.check(game_busy)
@commands.check(player_exists)
async def tempus(ctx, status: str):
    if status not in ["in", "ex"]:
        raise commands.CheckFailure(message="wrong tempus status")
    response = bot.spel.player_tempus(str(ctx.author), status)
    await ctx.channel.send(response)


@bot.command(name=UITDELEN, help="Zeg aan wie je drankeenheden wilt uitdelen en hoeveel. "
                                 f"Gebruik hiervoor het format\n'{PREFIX}{UITDELEN} speler1:drankhoeveelheid1 "
                                 f"speler2:drankhoeveelheid2 speler3:drankhoeveelheid3'\nenz. "
                                 "Hierbij zijn zowel speler als drankhoeveelheid een positief geheel getal. "
                                 f"Om te zien welke speler welk getal heeft, kan je '{PREFIX}{SPELERS}' gebruiken.")
@commands.check(game_busy)
@commands.check(player_exists)
@commands.check(game_started)
async def distribute(ctx, *, uitgedeeld):
    to_distribute = [x.split(":") for x in uitgedeeld.split(" ")]
    try:
        to_distribute = [(int(x), int(y)) for x, y in to_distribute]
    except Exception:
        raise commands.CheckFailure(message="wrong distribute call")
    if not all([[units > 0 for _, units in to_distribute]]):
        raise commands.CheckFailure(message="wrong distribute call")
    all_units = sum([units for _, units in to_distribute])
    if not bot.spel.check_player_distributor(str(ctx.author), all_units, zero_allowed=False):
        raise commands.CheckFailure(message="not enough drink units left")
    if all([player in range(len(bot.spel.players)) for player in [p for p, _ in to_distribute]]):
        for player, units in to_distribute:
            bot.spel.distributor(str(ctx.author), player, units)
        response = bot.spel.drink()
    else:
        response = "Een van de spelers die je probeert drank te geven bestaat niet. " \
                   f"Er zijn maar {len(bot.spel.players)} spelers. Probeer opnieuw."
    await ctx.channel.send(response)


"""
help=f"Als dit commando geactiveerd wordt met '{PREFIX}{DUBBELDRIEMAN} in', "
      "en een speler werpt een 2 en een 1 als deze al drieman is, "
      "dan drinkt de speler vanaf dan 2 drankeenheden per 3 op de dobbelstenen. "
      f"Met '{PREFIX}{DUBBELDRIEMAN} ex' kan dit gedeactiveerd worden.\n"
      "Je kan wel maximaal dubbeldrieman worden, er is niet zoiets als trippeldrieman bijvoorbeeld."
"""


@bot.command(name='dubbeldrieman', pass_context=True, hidden=True)
async def double_3man(ctx):
    if not (bot.spel is not None and isinstance(bot.spel, Game)):
        raise commands.errors.CommandNotFound()
    if str(ctx.author) not in [player.fullname for player in bot.spel.players]:
        raise commands.errors.CommandNotFound()
    status = ctx.message.content[-2:]
    if status not in ["in", "ex"]:
        raise commands.errors.CommandNotFound()
    await ctx.message.delete()
    if (status, bot.spel.dbldriemansetting) in [("ex", True), ("in", False)]:
        bot.spel.switch_dbldrieman_setting()
        if bot.spel.dbldriemansetting:
            response = "Er wordt gespeeld met de instelling 'dubbeldrieman'. " \
                       "Dit wil zeggen dat als je twee maal na elkaar drieman wordt, " \
                       "je ook tweemaal zoveel moet drinken. " \
                       "Elke drie die op de dobbelstenen tevoorschijn komt, betekent dan twee slokken voor de drieman."
        else:
            response = f"De instelling 'dubbeldrieman' staat nu terug uit."
    else:
        response = f"Je bent al in de modus '{DUBBELDRIEMAN} {status}'."
    await ctx.channel.send(response)


@bot.event
async def on_message(message):
    server = discord.utils.get(bot.guilds, name=SERVER)
    channel = discord.utils.get(server.channels, name=CHANNEL)
    if message.content == "3man help dubbeldrieman":
        await channel.send("De DriemanBot heeft geen commando 'dubbeldrieman'.")
        return
    await bot.process_commands(message)
    if message.author == bot.user or message.content != "vice kapot" or bot.spel is None:
        return
    if not isinstance(bot.spel, Game) or str(message.author) not in [player.fullname for player in bot.spel.players]:
        return
    if message.content == "vice kapot":
        await message.delete()
    with open('.secret', 'r') as file:
        access = [line.strip() for line in file]
    if str(message.author) not in access:
        return
    response = "@Kobe#5350\n" \
               f"Iemand (kuch kuck {message.author.mention}) vindt dat je nog niet zat genoeg bent.\n" \
               f"Wie ben ik, simpele bot die ik ben, om dit tegen te spreken?\n" \
               f"Daarom speciaal voor jou:"
    file = discord.File("vicekapot.png")
    embed = discord.Embed()
    embed.set_image(url="attachment://vicekapot.png")
    await channel.send(response, file=file, embed=embed)


@bot.event
async def on_error(error, *args, **kwargs):
    with open('err.txt', 'a') as f:
        f.write(f"{str(datetime.now())}\n{str(error)}\n")
        try:
            traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
        except Exception as exc:
            f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
            traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
        f.write("\n\n\n\n\n")
    server = discord.utils.get(bot.guilds, name=SERVER)
    channel = discord.utils.get(server.channels, name=CHANNEL)
    await channel.send(f"@here\n"
                       "Er is een fout opgetreden. Contacteer de beheerder van de DriemanBot.")


@bot.event
async def on_command_error(ctx, error):
    def write_error():
        with open('err.txt', 'a') as f:
            f.write(f"{str(ctx.message.created_at)}  {ctx.message.guild}  {ctx.message.channel.category}  "
                    f"{ctx.message.channel}  {ctx.message.author}  {ctx.message.content}\n"
                    f"{ctx.message.jump_url}\n{str(error)}\n")
            try:
                traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
            except Exception as exc:
                f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
                traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
            f.write("\n\n\n\n\n")

    server = discord.utils.get(bot.guilds, name=SERVER)
    channel = discord.utils.get(server.channels, name=CHANNEL)
    if isinstance(error, commands.errors.CheckFailure):
        if str(error) == "wrong channel or category":
            await channel.send(
                f"{ctx.author.mention}\n"
                f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention} onder '{CATEGORY}'.\n"
                f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention} "
                f"onder '{ctx.channel.category.name}'. Dat gaat helaas niet.")
        elif str(error) == "no active game":
            await channel.send(f"Er is geen spel bezig. Gebruik '{PREFIX}{MEEDOEN}' om als eerste mee te doen "
                               "of ga met iemand anders zijn voeten spelen.")
        elif str(error) == "game already started":
            await channel.send(f"Het spel is al begonnen. "
                               f"Als je een nieuw spel wil beginnen, gebruik dan eerst '{PREFIX}{STOP}'.")
        elif str(error) == "wrong nickname input":
            await channel.send(f"De bijnaam die je hebt ingegeven kan niet geaccepteerd worden, kies iets anders.")
        elif str(error) == "player doesn't exist":
            await channel.send(f"Je speelt nog niet mee met dit spel. Gebruik '{PREFIX}{MEEDOEN}' om mee te doen.\n"
                               f"Daarna kan je dit commando pas gebruiken.")
        elif str(error) == "player already exists":
            await channel.send(f"Je speelt al mee met dit spel. Gebruik '{PREFIX}{WEGGAAN}' om weg te gaan.\n"
                               f"Daarna kan je dit commando pas opnieuw gebruiken.")
        elif str(error) == "wrong tempus status":
            await channel.send(f"Je kan enkel '{PREFIX}{TEMPUS} in' of '{PREFIX}{TEMPUS} ex' gebruiken."
                               f"'{ctx.message.content}' is geen geldig tempus commando.")
        elif str(error) == "not your turn":
            await channel.send("Je bent nu niet aan de beurt, wacht alsjeblieft geduldig je beurt af.\n"
                               f"Het is nu de beurt aan {bot.spel.beurt.name}")
        elif str(error) == "game not started":
            await channel.send(f"Het spel is nog niet gestart. Gebruik eerst '{PREFIX}{START}' om het spel te starten.")
        elif str(error) == "not enough drink units left":
            await channel.send("Je hebt niet genoeg drankeenheden meer over om uit te delen.")
        elif str(error) == "wrong distribute call":
            await channel.send("Gebruik het juiste format om drankeenheden uit te delen, anders lukt het niet.")
        else:
            write_error()
            await channel.send(
                f"Het commando '{ctx.message.content}' heeft iets raar gedaan. "
                f"Contacteer de beheerder van de DriemanBot.")
    elif isinstance(error, commands.errors.CommandNotFound):
        if not (ctx.channel.name == CHANNEL and ctx.channel.category.name == CATEGORY):
            await channel.send(
                f"{ctx.author.mention}\n"
                f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention} onder '{CATEGORY}'.\n"
                f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention} "
                f"onder '{ctx.channel.category.name}'. Dat gaat helaas niet.")
        else:
            await channel.send(f"{ctx.author.mention}\n"
                               f"Het commando '{ctx.message.content}' is onbekend. "
                               "Contacteer de beheerder van de DriemanBot als je denkt dat dit zou moeten werken.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        response = f"Het commando '{ctx.message.content}' heeft een verplicht argument dat hier ontbreekt."
        if ctx.message.content[:len(PREFIX) + len(UITDELEN)] == PREFIX + UITDELEN:
            response += "\nGebruik het juiste format om drankeenheden uit te delen, anders lukt het niet."
        elif ctx.message.content[:len(PREFIX) + len(TEMPUS)] == PREFIX + TEMPUS:
            response += f"\n'{ctx.message.content}' is geen geldig tempus commando."
        await channel.send(response)
    else:
        write_error()
        await channel.send(
            f"{ctx.author.mention}\n"
            f"Het commando '{ctx.message.content}' is gefaald. Contacteer de beheerder van de DriemanBot.")


bot.run(TOKEN)  # TODO: add comments everywhere to explain what the code does
