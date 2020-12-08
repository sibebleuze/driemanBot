#!/usr/bin/env python3
import gc  # noqa
import os  # noqa
import traceback  # noqa
from datetime import datetime  # noqa

import discord  # noqa
from discord.ext import commands  # noqa
from dotenv import load_dotenv  # noqa

from gameplay.constants import *  # noqa
from gameplay.game import Game  # noqa
from gameplay.player import Player  # noqa

gc.enable()  # explicitely enable garbage collector
load_dotenv()  # load the Discord token as environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
# TODO: define server, channel and category by id instead of string name
SERVER = TEST_SERVER if TESTER else WINA_SERVER  # use different values when testing vs. when actually in use,
CHANNEL = TEST_CHANNEL if TESTER else DRIEMAN_CHANNEL  # these values all together determine server, channel
CATEGORY = TEST_CATEGORY if TESTER else DRIEMAN_CATEGORY  # and even category
MIN_PLAYERS = MIN_TESTERS if TESTER else MIN_PLAYERS  # and for testing we have less players available


class CustomHelpCommand(commands.DefaultHelpCommand):  # define a custom help command,
    def __init__(self, **options):
        options['no_category'] = "DriemanBot commando's"  # primarily to put some stuff in Dutch
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


help_command = CustomHelpCommand()  # initialize the custom help command
bot = commands.Bot(command_prefix=PREFIX, help_command=help_command)  # initialize the bot
bot.spel = Game()  # initialize the game


@bot.check  # global check for all commands
async def in_drieman_channel(ctx):  # check if command message is in correct channel and category
    if not (ctx.channel.name == CHANNEL and ctx.channel.category.name == CATEGORY):
        raise commands.CheckFailure(message="wrong channel or category")
    return True


@bot.check  # global check for all commands
async def oneliner(ctx):  # check if command message consists of one line only
    if "\n" in ctx.message.content:
        raise commands.CheckFailure(message="multiline message")
    return True


async def is_new_player(ctx):  # check if player doesn't already exist
    if str(ctx.author) in [player.fullname for player in bot.spel.players]:
        raise commands.CheckFailure(message="player already exists")
    return True


async def does_player_exist(ctx):  # check if player already exists
    if str(ctx.author) not in [player.fullname for player in bot.spel.players]:
        raise commands.CheckFailure(message="player doesn't exist")
    return True


async def can_you_roll(ctx):  # check if a player is allowed to roll the dice
    if not len(bot.spel.players) >= MIN_PLAYERS:  # not enough players joined yet to start playing
        raise commands.CheckFailure(message="not enough players")
    elif str(ctx.author) != bot.spel.beurt.fullname:  # it is not this players turn
        raise commands.CheckFailure(message="not your turn")
    return True


@bot.event
async def on_ready():  # the output here is only visible at server level and not in Discord
    if TESTER:  # when testing, display this message when the bot has started
        print(f'{bot.user.name} has connected to Discord!')  # print bot name
        server = discord.utils.get(bot.guilds, name=SERVER)  # find the correct server
        print(
            f'{bot.user.name} is connected to the following server:\n'
            f'{server.name} (id: {server.id})'
        )  # print server name and id
        channel = discord.utils.get(server.channels, name=CHANNEL)  # find the correct channel
        print(f'{bot.user.name} is limited to the channel:\n'
              f'{channel.name} (id: {channel.id})')  # print channel name and id
        members = '\n - '.join([member.name for member in server.members])  # find all member the bot has access to
        print(f'Visible Server Members:\n - {members}')  # print these members, if correct, this should be the bot only


@bot.command(name=REGELS, help='De link naar de regels printen.')
async def rules(ctx):  # print the link to the game rules to the channel
    await ctx.channel.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")


@bot.command(name=MEEDOEN, help="Jezelf toevoegen aan de lijst van actieve spelers.\n"
                                "Met het optionele argument 'bijnaam' kan je een bijnaam "
                                "bestaande uit 1 woord kiezen.")
@commands.check(is_new_player)
async def join(ctx, bijnaam=None):  # add a new player to the game
    response = ""
    if bijnaam is not None:  # if a nickname is given, check that it is correct
        if not (isinstance(bijnaam, str) and " " not in bijnaam and bijnaam != ""):  # no empty strings or spaces
            raise commands.CheckFailure(message="wrong nickname input")
    player = Player(ctx.author).set_nickname(bijnaam)  # initiate the Player and set its nickname
    if str(ctx.author) == 'Kobe#5350':  # temporary addition in code to try to capture vice mention
        VICE = ctx.author.mention  # set VICE to this new value
        with open('err.txt', 'a') as f:  # write it to errorlog
            f.write(f"vice mention gevonden: {VICE}\n\n\n\n\n")
    bot.spel.add_player(player)  # add the new Player object to the active player list
    if len(bot.spel.players) >= MIN_PLAYERS and bot.spel.beurt is None:  # when the minimum player limit is reached,
        bot.spel.beurt = bot.spel.players[0]  # initiate the turn to the first player who joined
    response += f"{player.name} ({player.nickname}) is in het spel gekomen."
    await ctx.channel.send(response)  # send the built up response to the channel


@bot.command(name=BIJNAAM, help='Stel je bijnaam in als je dat nog niet gedaan had '
                                'of wijzig je bijnaam als je een andere wilt.')
@commands.check(does_player_exist)
async def nickname(ctx, *, bijnaam: str):  # set another nickname for a player
    if " " in bijnaam or bijnaam == "":  # check that the nickname doesn't contain empty strings or spaces
        raise commands.CheckFailure(message="wrong nickname input")
    # find the correct Player in the list of active players
    player = bot.spel.players[[player.fullname for player in bot.spel.players].index(str(ctx.author))]
    player.set_nickname(bijnaam)  # set the nickname
    await ctx.channel.send(f"{player.name} heeft nu de bijnaam {player.nickname}.")  # send the response to the channel


@bot.command(name=WEGGAAN, help='Jezelf verwijderen uit de lijst van actieve spelers.')
@commands.check(does_player_exist)
async def leave(ctx):  # remove a player from the game
    response = bot.spel.remove_player(str(ctx.author))  # actual removing happens here
    if not bot.spel.players:  # if this was the last player, print a final message and start a new game
        response += "\nDe laatste speler heeft het spel verlaten. Het spel is nu afgelopen.\n" \
                    f"Een nieuw spel begint als er opnieuw {MIN_PLAYERS} spelers zijn."
        bot.spel = Game()
        gc.collect()  # explicitly collect garbage here, because we throw away all Game and Player objects here
    elif len(bot.spel.players) <= (MIN_PLAYERS - 1):  # if there are not enough players left, display this message
        response += "\nEr zijn niet genoeg spelers om verder te spelen.\n" \
                    "Wacht tot er opnieuw genoeg spelers zijn of beëindig het spel.\n" \
                    f"Een nieuwe speler kan meedoen door '{PREFIX}{MEEDOEN}' te typen.\n" \
                    f"Het spel kan beëindigd worden door '{PREFIX}{STOP}' te typen."
    await ctx.channel.send(response)  # send the built up response to the channel


@bot.command(name=STOP, help=f'Stop het spel als er minder dan {MIN_PLAYERS} actieve spelers zijn.')
async def stop(ctx):  # explicitly stop the game if not enough players are left
    response = ""
    if len(bot.spel.players) < MIN_PLAYERS:  # only possible when the amount of players falls below minimum
        for player in bot.spel.players:  # first, throw out all remaining players
            response += bot.spel.remove_player(player.fullname)
        response += "\nHet spel is nu afgelopen.\n" \
                    f"Een nieuw spel begint als er opnieuw {MIN_PLAYERS} spelers zijn."
        bot.spel = Game()  # print a final message and start a new game
        gc.collect()  # explicitly collect garbage here, because we throw away all Game and Player objects here
    else:  # if enough players are left to play, don't allow someone to just throw them all out
        response = f"Er zijn nog meer dan {MIN_PLAYERS - 1} spelers in het spel. " \
                   "Om te zorgen dat niet zomaar iedereen een actief spel kan afbreken," \
                   f"kan het commando '{PREFIX}{STOP}' pas gebruikt worden " \
                   f"als er minder dan {MIN_PLAYERS} overblijven. " \
                   "Als je echt het spel wil stoppen, " \
                   f"zal/zullen nog {len(bot.spel.players) - (MIN_PLAYERS - 1)} speler(s) het spel moeten verlaten."
    await ctx.channel.send(response)  # send the built up response to the channel


@bot.command(name=SPELERS, help='Geeft een lijst van alle actieve spelers.')
async def who_is_here(ctx):  # print an overview of all active players
    embed = discord.Embed(title='Overzicht actieve spelers')  # this is done in a Discord embed
    for i, player in enumerate(bot.spel.players):  # add all players individually
        embed.add_field(name=f'Speler: {i}',
                        value=f"Naam: {player.name}\nBijnaam: "
                              f"{player.nickname if player.nickname is not None else ''}\nTe drinken: "
                              f"{player.achterstand}\nUit te delen: {player.uitdelen}",
                        inline=True)  # player number, name, nickname, drinks to drink and to distribute are displayed
    response = ""
    if bot.spel.beurt is not None:  # show whose turn it is if a game is going
        response += f"{bot.spel.beurt.name} is aan de beurt."
    if bot.spel.drieman is not None:  # show who is drieman if there is one
        response += f" {bot.spel.drieman.name} is op dit moment drieman."
    await ctx.channel.send(response, embed=embed)  # send the built up response to the channel with embedded overview


@bot.command(name=ROL, help='Rol de dobbelsteen als het jouw beurt is.')
@commands.check(can_you_roll)
async def roll(ctx):  # rolling of the dice happens here
    response, url = bot.spel.roll(str(ctx.author))  # get response about dice rolls and potential files to include
    if url is not None:  # if there is a file to include, process it here
        file = discord.File(url)  # initiate the file
        embed = discord.Embed()  # initiate the embed
        embed.set_image(url="attachment://" + url)  # add the file to the embed as an attachment
        await ctx.channel.send(response, file=file, embed=embed)  # send the built up response to the channel with file
    else:  # if there is no file, just send the built up response to the channel
        await ctx.channel.send(response)


@bot.command(name=TEMPUS, help="DriemanBot houdt tijdelijk bij hoeveel je moet drinken "
                               "en deelt je dit mee aan het einde van je tempus. "
                               f"Gebruik '{PREFIX}{TEMPUS} in' om je tempus te beginnen en "
                               f"'{PREFIX}{TEMPUS} ex' om je tempus te eindigen en je achterstand te weten te komen.")
@commands.check(does_player_exist)
async def tempus(ctx, status: str):  # allow players to take a tempus
    if status not in ["in", "ex"]:  # one can only go in or out (ex) of tempus, nothing else
        raise commands.CheckFailure(message="wrong tempus status")
    response = bot.spel.player_tempus(str(ctx.author), status)  # do the actual tempus switching and get response
    await ctx.channel.send(response)  # send the built up response to the channel


@bot.command(name=UITDELEN, help="Zeg aan wie je drankeenheden wilt uitdelen en hoeveel.\n"
                                 f"Gebruik hiervoor het format\n'{PREFIX}{UITDELEN} speler1:drankhoeveelheid1 "
                                 f"speler2:drankhoeveelheid2 speler3:drankhoeveelheid3'\nenz. "
                                 "Hierbij zijn zowel speler als drankhoeveelheid een positief geheel getal. "
                                 f"Om te zien welke speler welk getal heeft, kan je '{PREFIX}{SPELERS}' gebruiken.")
@commands.check(does_player_exist)
async def distribute(ctx, *, uitgedeeld: str):  # distribute an amount of drinking units to other players
    to_distribute = [x.split(":") for x in uitgedeeld.split(" ")]  # split handouts for different players and amounts
    try:  # try to make integers out of everything
        to_distribute = [(int(x), int(y)) for x, y in to_distribute]
    except Exception:  # if this fails, the input was wrong
        raise commands.CheckFailure(message="wrong distribute call")
    if not all([[units > 0 for _, units in to_distribute]]):  # you can't hand out a negative amount of drinking units
        raise commands.CheckFailure(message="wrong distribute call")
    all_units = sum([units for _, units in to_distribute])  # you can't hand out more units than you have left
    if not bot.spel.check_player_distributor(str(ctx.author), all_units, zero_allowed=False):  # so if you try to,
        raise commands.CheckFailure(message="not enough drink units left")  # you will be stopped
    # you can only distribute drinking units to players that exist
    if all([player in range(len(bot.spel.players)) for player in [p for p, _ in to_distribute]]):
        for player, units in to_distribute:  # distribute all units
            bot.spel.distributor(str(ctx.author), player, units)
        response = bot.spel.drink()  # get all people that should drink
    else:  # if one of them doesn't exist, you will be stopped
        response = "Een van de spelers die je probeert drank te geven bestaat niet. " \
                   f"Er zijn maar {len(bot.spel.players)} spelers. Probeer opnieuw."
    await ctx.channel.send(response)  # send the built up response to the channel


"""
# this help is for the dubbeldrieman command, but it wouldn't be hidden very well if it just
# showed up in the help section now would it
help=f"Als dit commando geactiveerd wordt met '{PREFIX}{DUBBELDRIEMAN} in', "
      "en een speler werpt een 2 en een 1 als deze al drieman is, "
      "dan drinkt de speler vanaf dan 2 drankeenheden per 3 op de dobbelstenen. "
      f"Met '{PREFIX}{DUBBELDRIEMAN} ex' kan dit gedeactiveerd worden.\n"
      "Je kan wel maximaal dubbeldrieman worden, er is niet zoiets als trippeldrieman bijvoorbeeld."
"""


@bot.command(name='dubbeldrieman', pass_context=True, hidden=True)
async def double_3man(ctx):  # activate the dubbeldrieman setting
    if str(ctx.author) not in [player.fullname for player in bot.spel.players]:  # only active players can do this
        raise commands.errors.CommandNotFound()
    status = ctx.message.content[-2:]
    if status not in ["in", "ex"]:  # one can only go in or out (ex) of this mode, nothing else
        raise commands.errors.CommandNotFound()
    await ctx.message.delete()  # hide the existence of this command
    if (status, bot.spel.dbldriemansetting) in [("ex", True), ("in", False)]:  # if the game isn't in the desired state
        bot.spel.switch_dbldrieman_setting()  # switch the setting
        if bot.spel.dbldriemansetting:  # define a message addressing the player for the bot to send
            response = "Er wordt gespeeld met de instelling 'dubbeldrieman'. " \
                       "Dit wil zeggen dat als je twee maal na elkaar drieman wordt, " \
                       "je ook tweemaal zoveel moet drinken. " \
                       "Elke drie die op de dobbelstenen tevoorschijn komt, betekent dan twee slokken voor de drieman."
        else:  # define a message addressing the player for the bot to send
            response = f"De instelling 'dubbeldrieman' staat nu terug uit."
    else:  # tell player he already has what he wants
        response = f"Je bent al in de modus '{DUBBELDRIEMAN} {status}'."
    await ctx.channel.send(response)  # send the built up response to the channel


@bot.event
async def on_message(message):
    server = discord.utils.get(bot.guilds, name=SERVER)  # find the correct server
    channel = discord.utils.get(server.channels, name=CHANNEL)  # find the correct channel
    if message.content == "3man help dubbeldrieman":  # hide the help response from this command
        # this needs to be done separately here in order to hide the command correctly
        if not (message.channel.name == CHANNEL and message.channel.category.name == CATEGORY):
            await channel.send(
                f"{message.author.mention}\n"
                f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention} onder '{CATEGORY}'.\n"
                f"Je probeerde de DriemanBot te gebruiken in het kanaal {message.channel.mention} "
                f"onder '{message.channel.category.name}'. Dat gaat helaas niet.")
        else:
            await channel.send("De DriemanBot heeft geen commando 'dubbeldrieman'.")
        return
    await bot.process_commands(message)  # process all other commands first, if they got nothing, only then proceed
    if message.author == bot.user or message.content != "vice kapot":  # only respond to this message
        return
    with open('bot/.secret', 'r') as file:  # get the access list for this command from the .secret file
        access = [line.strip() for line in file]
    if str(message.author) not in access:  # look up in the list if the user has the correct access
        return
    if message.content == "vice kapot":  # delete all trace of the messages existence if it got this far
        await message.delete()
    if str(message.author) not in [player.fullname for player in bot.spel.players]:  # only respond to active players
        return
    response = f"{VICE}\n" \
               f"Iemand (kuch kuck {message.author.mention}) vindt dat je nog niet zat genoeg bent.\n" \
               f"Wie ben ik, simpele bot die ik ben, om dit tegen te spreken?\n" \
               f"Daarom speciaal voor jou:"
    file = discord.File("pictures/vicekapot.png")  # special message for the vice, with a picture too
    embed = discord.Embed()
    embed.set_image(url="attachment://vicekapot.png")
    await channel.send(response, file=file, embed=embed)  # send the built up response to the channel with the file


@bot.event
async def on_error(error, *args, **kwargs):  # general error handling happens here
    with open('err.txt', 'a') as f:  # open the error log file
        f.write(f"{str(datetime.now())}\n{str(error)}\n")  # write the date, time and error
        try:  # try to also write the error traceback
            traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
        except Exception as exc:  # if this fails, print the error of this fail instead
            f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
            traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
        f.write("\n\n\n\n\n")  # some whitespace to distinguish different errors
    server = discord.utils.get(bot.guilds, name=SERVER)  # find the correct server
    channel = discord.utils.get(server.channels, name=CHANNEL)  # find the correct channel
    await channel.send(f"{PROGRAMMER}, er is een fout opgetreden.")  # send error message and mention me


@bot.event
async def on_command_error(ctx, error):  # command error handling happens here
    def write_error():  # function for writing errors to error log
        with open('err.txt', 'a') as f:  # open the file to append
            f.write(f"{str(ctx.message.created_at)}  {ctx.message.guild}  {ctx.message.channel.category}  "
                    f"{ctx.message.channel}  {ctx.message.author}  {ctx.message.content}\n"
                    f"{ctx.message.jump_url}\n{str(error)}\n")  # write some info on what caused the error
            try:  # try to also write the error traceback
                traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
            except Exception as exc:  # if this fails, print the error of this fail instead
                f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
                traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
            f.write("\n\n\n\n\n")  # some whitespace to distinguish different errors

    server = discord.utils.get(bot.guilds, name=SERVER)  # find the correct server
    channel = discord.utils.get(server.channels, name=CHANNEL)  # find the correct channel
    if isinstance(error, commands.errors.CheckFailure):  # one of the checks failed, someone did something wrong
        # below check failures are pretty self explanatory
        if str(error) == "wrong channel or category":
            await channel.send(
                f"{ctx.author.mention}\n"
                f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention} onder '{CATEGORY}'.\n"
                f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention} "
                f"onder '{ctx.channel.category.name}'. Dat gaat helaas niet.")
        elif str(error) == "multiline message":
            await channel.send(f"{ctx.author.mention}\n"
                               f"De DriemanBot accepteert enkel commando's die bestaan uit een enkele lijn.")
        elif str(error) == "wrong nickname input":
            await channel.send(f"De bijnaam die je hebt ingegeven kan niet geaccepteerd worden, kies iets anders.")
        elif str(error) == "player doesn't exist":
            await channel.send(f"Je speelt nog niet mee. Gebruik '{PREFIX}{MEEDOEN}' om mee te doen.\n"
                               f"Daarna kan je dit commando pas gebruiken.")
        elif str(error) == "player already exists":
            await channel.send(f"Je speelt al mee. Gebruik '{PREFIX}{WEGGAAN}' om weg te gaan.\n"
                               f"Daarna kan je dit commando pas opnieuw gebruiken.")
        elif str(error) == "wrong tempus status":
            await channel.send(f"Je kan enkel '{PREFIX}{TEMPUS} in' of '{PREFIX}{TEMPUS} ex' gebruiken."
                               f"'{ctx.message.content}' is geen geldig tempus commando.")
        elif str(error) == "not your turn":
            await channel.send("Je bent nu niet aan de beurt, wacht alsjeblieft geduldig je beurt af.\n"
                               f"Het is nu de beurt aan {bot.spel.beurt.name}")
        elif str(error) == "not enough players":
            await channel.send("Nog niet genoeg spelers, "
                               f"je moet minstens met {MIN_PLAYERS} zijn om te kunnen driemannen (zie art. 1).\n"
                               f"Wacht tot er nog {MIN_PLAYERS - len(bot.spel.players)} speler(s) "
                               f"meer meedoet/meedoen.")
        elif str(error) == "not enough drink units left":
            await channel.send("Je hebt niet genoeg drankeenheden meer over om uit te delen.")
        elif str(error) == "wrong distribute call":
            await channel.send("Gebruik het juiste format om drankeenheden uit te delen, anders lukt het niet.")
        else:  # in case it isn't one of the above cases, something actually went wrong
            write_error()  # in this case, write the error to the error log and alert me with a mention
            await channel.send(f"{PROGRAMMER}, het commando '{ctx.message.content}' heeft iets raar gedaan.")
    elif isinstance(error, commands.errors.CommandNotFound):  # someone entered a non existing command
        if not (ctx.channel.name == CHANNEL and ctx.channel.category.name == CATEGORY):  # in the wrong channel
            await channel.send(
                f"{ctx.author.mention}\n"
                f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention} onder '{CATEGORY}'.\n"
                f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention} "
                f"onder '{ctx.channel.category.name}'. Dat gaat helaas niet.")
        else:  # or in the correct one, either way it's not my problem until they make it my problem
            await channel.send(f"{ctx.author.mention}\n"
                               f"Het commando '{ctx.message.content}' is onbekend. "
                               "Contacteer de beheerder van de DriemanBot als je denkt dat dit zou moeten werken.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):  # also pretty self explanatory
        response = f"Het commando '{ctx.message.content}' heeft een verplicht argument dat hier ontbreekt."
        if ctx.message.content[:len(PREFIX) + len(UITDELEN)] == PREFIX + UITDELEN:
            response += "\nGebruik het juiste format om drankeenheden uit te delen, anders lukt het niet." \
                        f"Met '{PREFIX} help {UITDELEN}' kan je zien hoe het moet."
        elif ctx.message.content[:len(PREFIX) + len(TEMPUS)] == PREFIX + TEMPUS:
            response += f"\n'{ctx.message.content}' is geen geldig tempus commando."
        await channel.send(response)  # tell them what they did wrong
    else:  # something actually went wrong
        write_error()  # in this case, write the error to the error log and alert me with a mention
        await channel.send(f"{PROGRAMMER}, het commando '{ctx.message.content}' is gefaald.")


bot.run(TOKEN)
