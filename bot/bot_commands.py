#!/usr/bin/env python3
import gc  # noqa
import traceback  # noqa
from copy import deepcopy  # noqa
from datetime import datetime  # noqa

import discord  # noqa
from discord.ext import commands  # noqa

import gameplay.constants as const  # noqa
from gameplay.game import Game  # noqa
from gameplay.player import Player  # noqa

# use different values when testing vs. when actually in use, these values all together determine server, channel
# and even category, all by unique IDs and for testing we have less players available
SERVER = const.TEST_SERVER if const.TESTER else const.USER_SERVER
CHANNEL = const.TEST_CHANNEL if const.TESTER else const.DRIEMAN_CHANNEL
CATEGORY = const.TEST_CATEGORY if const.TESTER else const.DRIEMAN_CATEGORY
MIN_PLAYERS = const.MIN_TESTERS if const.TESTER else const.MIN_PLAYERS


class Comms(commands.Cog, name="DriemanBot commando's"):
    def __init__(self, bot):
        bot.spel = Game()  # initialize the game
        self.bot = bot
        self.time = datetime.now()

    def in_drieman_channel(self, ctx):  # check if command message is in correct channel and category
        if not (ctx.channel.id == CHANNEL and ctx.channel.category.id == CATEGORY):
            raise commands.CheckFailure(message="wrong channel or category")
        return True

    def oneliner(self, ctx):  # check if command message consists of one line only
        if "\n" in ctx.message.content:
            raise commands.CheckFailure(message="multiline message")
        return True

    def bot_check(self, ctx):  # global checks that apply to every command of the bot
        return self.in_drieman_channel(ctx) and self.oneliner(ctx)

    # functions in a class expect an argument self, but checks only provide ctx,
    # so in this way the checks can still be included in the cog
    def is_new_player(self):  # check if player doesn't already exist
        def predicate(ctx):
            if str(ctx.author) in [player.fullname for player in ctx.bot.spel.players]:
                raise commands.CheckFailure(message="player already exists")
            return True

        return commands.check(predicate)

    def does_player_exist(self):  # check if player already exists
        def predicate(ctx):
            if str(ctx.author) not in [player.fullname for player in ctx.bot.spel.players]:
                raise commands.CheckFailure(message="player doesn't exist")
            return True

        return commands.check(predicate)

    def can_you_roll(self):  # check if a player is allowed to roll the dice
        def predicate(ctx):
            if not len(ctx.bot.spel.players) >= MIN_PLAYERS:  # not enough players joined yet to start playing
                raise commands.CheckFailure(message="not enough players")
            elif str(ctx.author) != ctx.bot.spel.beurt.fullname:  # it is not this players turn
                raise commands.CheckFailure(message="not your turn")
            return True

        return commands.check(predicate)

    @commands.Cog.listener()
    async def on_ready(self):  # the output here is only visible at server level and not in Discord
        server = discord.utils.get(self.bot.guilds, id=SERVER)  # find the correct server
        channel = discord.utils.get(server.channels, id=CHANNEL)  # find the correct channel
        # print these messages in shell when the bot has started
        print(f'{self.bot.user.name} ({self.time}) has connected to Discord!')  # print bot name
        print(f'{self.bot.user.name} is connected to the following server:\n'
              f'{server.name} (id: {server.id})')  # print server name and id
        print(f'{self.bot.user.name} is limited to the channel:\n'
              f'{channel.name} (id: {channel.id})'
              f'\nunder {channel.category.name} (id: {channel.category.id})')  # print channel name and id
        members = '\n - '.join([member.name for member in server.members])  # find all members the bot has access to
        # print these members, if correct, this should be the bot only
        print(f'Visible Server Members:\n - {members}')
        messages = await channel.history().flatten()
        newest = sorted(messages, key=lambda x: x.created_at)[-1]
        for message in messages:
            if message.content == "De DriemanBot staat uit." and message.author == self.bot.user:
                await message.delete()
            elif message.content == "De DriemanBot staat aan." and message.author == self.bot.user:
                if message != newest:
                    await message.delete()
        if newest.content != "De DriemanBot staat aan.":
            await channel.send("De DriemanBot staat aan.")  # let bot users know the bot is online

    @commands.Cog.listener()
    async def on_disconnect(self):  # the output here is only visible at server level and not in Discord
        print(f"{self.bot.user.name} ({self.time}) is offline gegaan om {datetime.now()}.")
        server = discord.utils.get(self.bot.guilds, id=SERVER)  # find the correct server
        channel = discord.utils.get(server.channels, id=CHANNEL)  # find the correct channel
        while not self.bot.ws.open:
            await channel.history().flatten()
        print(f"{self.bot.user.name} ({self.time}) is terug online gekomen om {datetime.now()}.")

    @commands.command(pass_context=True, hidden=True)
    async def power(self, ctx, status):  # command to shutdown or restart the bot
        if ctx.author.mention == const.PROGRAMMER:  # for one person only (same one that gets all the error messages)
            if status not in ["on", "off"]:
                raise commands.errors.CommandNotFound  # mistyped, just give a command not found, easy to figure out
            else:
                await ctx.message.delete()  # hide the existence of this command a bit, since no one else can use it
                if status == "off":  # shutdown
                    self.bot.shutdown = True  # will break the surrounding while loop and shut down the python script
                messages = await ctx.channel.history().flatten()
                for message in messages:
                    if message.content == "De DriemanBot staat aan." and message.author == ctx.bot.user:
                        await message.delete()
                    elif "3man power off" in message.content or "3man power on" in message.content:
                        await message.delete()
                    elif message.content == "De DriemanBot staat uit." and message.author == ctx.bot.user:
                        await message.delete()
                await ctx.channel.send("De DriemanBot staat uit.")  # message to let people know the bot is gone
                await self.bot.logout()  # actual shutdown
                t = self.bot.cogs["DriemanBot commando's"].time
                print(f"{self.bot.user.name} ({t}) is offline.")  # confirmation of being offline in shell
        else:
            await ctx.channel.send("Ontoereikende permissies")  # tell other people what they're doing wrong

    @commands.command(name=const.REGELS, help='De link naar de regels printen.')
    async def rules(self, ctx):  # print the link to the game rules to the channel
        await ctx.channel.send("Je kan de regels vinden op https://wina-gent.be/drieman.pdf.")

    @commands.command(name=const.MEEDOEN, help="Jezelf toevoegen aan de lijst van actieve spelers.\n"
                                               "Met het optionele argument 'naam' kan je een naam "
                                               "bestaande uit 1 woord kiezen.")
    @is_new_player("self")  # @commands.check(is_new_player)
    async def join(self, ctx, bijnaam=None):  # add a new player to the game
        response = ""
        if bijnaam is not None:  # if a nickname is given, check that it is correct
            if not (isinstance(bijnaam, str) and " " not in bijnaam and bijnaam != ""):  # no empty strings or spaces
                raise commands.CheckFailure(message="wrong nickname input")
        player = Player(ctx.author).set_nickname(bijnaam)  # initiate the Player and set its nickname
        ctx.bot.spel.add_player(player)  # add the new Player object to the active player list
        if len(ctx.bot.spel.players) >= MIN_PLAYERS and ctx.bot.spel.beurt is None:
            # when the minimum player limit is reached, initiate the turn to the first player who joined
            ctx.bot.spel.beurt = ctx.bot.spel.players[0]
        response += f"{player.name} ({player.nickname}) is in het spel gekomen."
        await ctx.channel.send(response)  # send the built up response to the channel

    @commands.command(name=const.BIJNAAM, help='Stel je naam in als je dat nog niet gedaan had '
                                               'of wijzig je naam als je een andere wilt.')
    @does_player_exist("self")  # @commands.check(does_player_exist)
    async def nickname(self, ctx, *, bijnaam: str):  # set another nickname for a player
        if " " in bijnaam or bijnaam == "":  # check that the nickname doesn't contain empty strings or spaces
            raise commands.CheckFailure(message="wrong nickname input")
        # find the correct Player in the list of active players
        player = ctx.bot.spel.players[[player.fullname for player in ctx.bot.spel.players].index(str(ctx.author))]
        player.set_nickname(bijnaam)  # set the nickname
        await ctx.channel.send(
            f"{player.name} heeft nu de naam {player.nickname}.")  # send the response to the channel

    @commands.command(name=const.WEGGAAN, help='Jezelf verwijderen uit de lijst van actieve spelers.')
    @does_player_exist("self")  # @commands.check(does_player_exist)
    async def leave(self, ctx):  # remove a player from the game
        response = ctx.bot.spel.remove_player(str(ctx.author))  # actual removing happens here
        if not ctx.bot.spel.players:  # if this was the last player, print a final message and start a new game
            response += "\nDe laatste speler heeft het spel verlaten. Het spel is nu afgelopen.\n" \
                        f"Een nieuw spel begint als er opnieuw {MIN_PLAYERS} spelers zijn."
            ctx.bot.spel = Game()
            gc.collect()  # explicitly collect garbage here, because we throw away all Game and Player objects here
        elif len(ctx.bot.spel.players) <= (
                MIN_PLAYERS - 1):  # if there are not enough players left, display this message
            response += "\nEr zijn niet genoeg spelers om verder te spelen.\n" \
                        "Wacht tot er opnieuw genoeg spelers zijn of beëindig het spel.\n" \
                        f"Een nieuwe speler kan meedoen door '{const.PREFIX}{const.MEEDOEN}' te typen.\n" \
                        f"Het spel kan beëindigd worden door '{const.PREFIX}{const.STOP}' te typen."
        await ctx.channel.send(response)  # send the built up response to the channel

    @commands.command(name=const.STOP, help=f'Stop het spel als er minder dan {MIN_PLAYERS} actieve spelers zijn.')
    async def stop(self, ctx):  # explicitly stop the game if not enough players are left
        response = ""
        if len(ctx.bot.spel.players) < MIN_PLAYERS:  # only possible when the amount of players falls below minimum
            # first, throw out all remaining players; deepcopy because removing stuff from lists fucks things up
            response += "\n".join(
                [ctx.bot.spel.remove_player(player.fullname) for player in deepcopy(ctx.bot.spel.players)])
            response += "\nHet spel is nu afgelopen.\n" \
                        f"Een nieuw spel begint als er opnieuw {MIN_PLAYERS} spelers zijn."
            ctx.bot.spel = Game()  # print a final message and start a new game
            gc.collect()  # explicitly collect garbage here, because we throw away all Game and Player objects here
        else:  # if enough players are left to play, don't allow someone to just throw them all out
            response = f"Er zijn nog meer dan {MIN_PLAYERS - 1} spelers in het spel. " \
                       "Om te zorgen dat niet zomaar iedereen een actief spel kan afbreken, " \
                       f"kan het commando '{const.PREFIX}{const.STOP}' pas gebruikt worden " \
                       f"als er minder dan {MIN_PLAYERS} overblijven. " \
                       "Als je echt het spel wil stoppen, " \
                       f"zal/zullen nog {len(ctx.bot.spel.players) - (MIN_PLAYERS - 1)} " \
                       f"speler(s) het spel moeten verlaten."
        await ctx.channel.send(response)  # send the built up response to the channel

    @commands.command(name=const.SPELERS, help='Geeft een lijst van alle actieve spelers.')
    async def who_is_here(self, ctx):  # print an overview of all active players
        embed = discord.Embed(title='Overzicht actieve spelers')  # this is done in a Discord embed
        for i, player in enumerate(ctx.bot.spel.players):  # add all players individually
            # player number, name, nickname, drinks to drink and to distribute are displayed
            embed.add_field(name=f'Speler: {i}',
                            value=f"Naam: {player.nickname if player.nickname is not None else player.fullname[:-5]}\n"
                                  f"Gedronken: {player.totaal}\nUit te delen: {player.uitdelen}\nDriemangetal: "
                                  f"{player.driemannumber}", inline=True)
        response = ""
        if ctx.bot.spel.beurt is not None:  # show whose turn it is if a game is going
            response += f"{ctx.bot.spel.beurt.name} is aan de beurt."
        if ctx.bot.spel.drieman is not None:  # show who is drieman if there is one
            response += f" {ctx.bot.spel.drieman.name} is op dit moment drieman."
        await ctx.channel.send(response,
                               embed=embed)  # send the built up response to the channel with embedded overview

    @commands.command(name=const.ROL, help='Rol de dobbelsteen als het jouw beurt is.')
    @can_you_roll("self")  # @commands.check(can_you_roll)
    async def roll(self, ctx):  # rolling of the dice happens here
        response, url = ctx.bot.spel.roll(
            str(ctx.author))  # get response about dice rolls and potential files to include
        if url is not None:  # if there is a file to include, process it here
            file = discord.File(url)  # initiate the file
            embed = discord.Embed()  # initiate the embed
            embed.set_image(url="attachment://" + url)  # add the file to the embed as an attachment
            await ctx.channel.send(response, file=file,
                                   embed=embed)  # send the built up response to the channel with file
        else:  # if there is no file, just send the built up response to the channel
            await ctx.channel.send(response)

    @commands.command(name=const.TEMPUS, help="DriemanBot houdt tijdelijk bij hoeveel je moet drinken "
                                              "en deelt je dit mee aan het einde van je tempus. "
                                              f"Gebruik '{const.PREFIX}{const.TEMPUS} in' om je tempus te beginnen en "
                                              f"'{const.PREFIX}{const.TEMPUS} ex' om je tempus te eindigen en "
                                              "je achterstand te weten te komen.")
    @does_player_exist("self")  # @commands.check(does_player_exist)
    async def tempus(self, ctx, status: str):  # allow players to take a tempus
        if status not in ["in", "ex"]:  # one can only go in or out (ex) of tempus, nothing else
            raise commands.CheckFailure(message="wrong tempus status")
        response = ctx.bot.spel.player_tempus(str(ctx.author),
                                              status)  # do the actual tempus switching and get response
        await ctx.channel.send(response)  # send the built up response to the channel

    @commands.command(name=const.UITDELEN, help="Zeg aan wie je drankeenheden wilt uitdelen en hoeveel.\n"
                                                f"Gebruik hiervoor het format\n'{const.PREFIX}{const.UITDELEN} "
                                                f"speler1:drankhoeveelheid1 speler2:drankhoeveelheid2 "
                                                f"speler3:drankhoeveelheid3'\nenz. Hierbij is drankhoeveelheid een "
                                                f"positief geheel getal. Voor speler kan je ofwel een volgnummer "
                                                f"gebruiken, ofwel de speler taggen (met @speler). Om te zien wie er "
                                                f"allemaal meedoet, kan je '{const.PREFIX}{const.SPELERS}' gebruiken.")
    @does_player_exist("self")  # @commands.check(does_player_exist)
    async def distribute(self, ctx, *, uitgedeeld: str):  # distribute an amount of drinking units to other players
        while ' :' in uitgedeeld:
            uitgedeeld = uitgedeeld.replace(' :', ':')
        to_distribute = [x.split(":") for x in
                         uitgedeeld.split(" ")]  # split handouts for different players and amounts
        try:
            to_distribute = [[(person if person.isnumeric() else (
                person if person not in [player.name for player in self.bot.spel.players] else [player.name for player
                                                                                                in
                                                                                                self.bot.spel.players].index(
                    person))), units] for person, units in
                             to_distribute]  # allow mentions instead of player index numbers
            to_distribute = [(int(x), int(y)) for x, y in to_distribute]  # try to make integers out of everything
        except Exception:  # if this fails, the input was wrong
            raise commands.CheckFailure(message="wrong distribute call")
        if not all(
                [[units > 0 for _, units in to_distribute]]):  # you can't hand out a negative amount of drinking units
            raise commands.CheckFailure(message="wrong distribute call")
        all_units = sum([units for _, units in to_distribute])  # you can't hand out more units than you have left
        if not ctx.bot.spel.check_player_distributor(str(ctx.author), all_units,
                                                     zero_allowed=False):  # so if you try to,
            raise commands.CheckFailure(message="not enough drink units left")  # you will be stopped
        # you can only distribute drinking units to players that exist
        if all([player in range(len(ctx.bot.spel.players)) for player in [p for p, _ in to_distribute]]):
            for player, units in to_distribute:  # distribute all units
                ctx.bot.spel.distributor(str(ctx.author), player, units)
            response = ctx.bot.spel.drink()  # get all people that should drink
        else:  # if one of them doesn't exist, you will be stopped
            response = "Een van de spelers die je probeert drank te geven bestaat niet. " \
                       f"Er zijn maar {len(ctx.bot.spel.players)} spelers. Probeer opnieuw."
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

    @commands.command(name='dubbeldrieman', pass_context=True, hidden=True)
    async def double_3man(self, ctx):  # activate the dubbeldrieman setting
        if str(ctx.author) not in [player.fullname for player in
                                   ctx.bot.spel.players]:  # only active players can do this
            raise commands.errors.CommandNotFound()
        status = ctx.message.content[-2:]
        if status not in ["in", "ex"]:  # one can only go in or out (ex) of this mode, nothing else
            raise commands.errors.CommandNotFound()
        await ctx.message.delete()  # hide the existence of this command
        if (status, ctx.bot.spel.dbldriemansetting) in [("ex", True),
                                                        ("in", False)]:  # if the game isn't in the desired state
            ctx.bot.spel.switch_dbldrieman_setting()  # switch the setting
            if ctx.bot.spel.dbldriemansetting:  # define a message addressing the player for the bot to send
                response = "Er wordt gespeeld met de instelling 'dubbeldrieman'. " \
                           "Dit wil zeggen dat als je twee maal na elkaar drieman wordt, " \
                           "je ook tweemaal zoveel moet drinken. " \
                           "Elke drie die op de dobbelstenen tevoorschijn komt, " \
                           "betekent dan twee slokken voor de drieman."
            else:  # define a message addressing the player for the bot to send
                response = f"De instelling 'dubbeldrieman' staat nu terug uit."
        else:  # tell player he already has what he wants
            response = f"Je bent al in de modus '{const.DUBBELDRIEMAN} {status}'."
        await ctx.channel.send(response)  # send the built up response to the channel

    @commands.command(name='koprol', hidden=True)
    async def koprol(self, ctx):
        with open('../bot/.secret', 'r') as file:  # get the access list for this command from the .secret file
            access = [line.strip() for line in file]
        if str(ctx.author) not in access:  # look up in the list if the user has the correct access
            await ctx.channel.send(f"Ik dacht het niet, {ctx.author.mention}.")
        else:
            pic = "../pictures/koprol.gif"
            file = discord.File(pic)  # special gif
            embed = discord.Embed()
            embed.set_image(url="attachment://" + pic)
            await ctx.channel.send(file=file, embed=embed)  # send the file to the channel

    @commands.command(name='skip', hidden=True)
    async def skip(self, ctx):
        if ctx.author.mention == const.PROGRAMMER:  # for one person only (same one that gets all the error messages)
            await ctx.message.delete()  # hide the existence of this command a bit, since no one else can use it
            await ctx.channel.send(f"{self.bot.spel.beurt.name}, je doet er te lang over om te spelen, daarom ben "
                                   f"je even overgeslagen. Je hebt nu drie keuzes; kom terug meedoen, neem een tempus "
                                   f"of verlaat het spel. Bij herhaaldelijk je beurt missen zal {const.PROGRAMMER} je "
                                   f"uit het spel verwijderen.")
            self.bot.spel.beurt = self.bot.spel.beurt.next_player  # the turn goes to the next person
            while self.bot.spel.beurt.tempus and not all([p.tempus for p in self.bot.spel.players]):
                self.bot.spel.beurt = self.bot.spel.beurt.next_player
            await ctx.channel.send(f"{self.bot.spel.beurt.name} is nu aan de beurt.")
        else:
            await ctx.channel.send("Ontoereikende permissies")  # tell other people what they're doing wrong

    @commands.command(name='buitenwipper', hidden=True)
    async def eject(self, ctx):
        if ctx.author.mention == const.PROGRAMMER:  # for one person only (same one that gets all the error messages)
            await ctx.message.delete()  # hide the existence of this command a bit, since no one else can use it
            await ctx.channel.send(f"{self.bot.spel.beurt.name}, je bent te lang inactief geweest in het spel en "
                                   f"waarschijnlijk heb je ook al 1 of meer beurten gemist. Daarom heeft "
                                   f"{const.PROGRAMMER} besloten om je eruit te gooien. Je kan opnieuw meedoen, maar "
                                   f"let dan wel op alsjeblieft.")
            response = self.bot.spel.remove_player(self.bot.spel.beurt.fullname)  # actual removing happens here
            await ctx.channel.send(response)  # send the built up response to the channel
            await ctx.channel.send(f"{self.bot.spel.beurt.name} is nu aan de beurt.")
        else:
            await ctx.channel.send("Ontoereikende permissies")  # tell other people what they're doing wrong

    @commands.Cog.listener()
    async def on_message(self, message):
        server = discord.utils.get(self.bot.guilds, id=SERVER)  # find the correct server
        channel = discord.utils.get(server.channels, id=CHANNEL)  # find the correct channel
        if message.content == "3man help dubbeldrieman":  # hide the help response from this command
            # this needs to be done separately here in order to hide the command correctly
            if not (message.channel.id == CHANNEL and message.channel.category.id == CATEGORY):
                await channel.send(f"{message.author.mention}\n"
                                   f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention}. "
                                   f"Je probeerde de DriemanBot te gebruiken in het kanaal {message.channel.mention}. "
                                   f"Dat gaat helaas niet.")
            else:
                await channel.send("De DriemanBot heeft geen commando 'dubbeldrieman'.")
            return
        await self.bot.process_commands(
            message)  # process all other commands first, if they got nothing, only then proceed
        if message.author != self.bot.user and message.content != "vice kapot":
            messages = await channel.history(limit=25).flatten()
            mssgs = []
            for mssg in messages:  # check if someone is spamming the channel with non game related messages
                if mssg.author == message.author and mssg.content == message.content and '3man ' not in mssg.content:
                    mssgs.append(mssg)
            if len(mssgs) > 3:  # is someone is spamming the channel, delete these spam messages
                for mssg in mssgs:
                    await mssg.delete()
                await channel.send(f"{message.author.mention}, alleen ik mag dit kanaal volspammen.")
        if message.author == self.bot.user or message.content != "vice kapot":  # only respond to this message
            return
        with open('../bot/.secret', 'r') as file:  # get the access list for this command from the .secret file
            access = [line.strip() for line in file]
        if str(message.author) not in access:  # look up in the list if the user has the correct access
            return
        if message.content == "vice kapot":  # delete all trace of the messages existence if it got this far
            await message.delete()
        if str(message.author) not in [player.fullname for player in
                                       self.bot.spel.players]:  # only respond to active players
            return
        response = f"{const.VICE}\n" \
                   f"Iemand (kuch kuck {message.author.mention}) vindt dat je nog niet zat genoeg bent.\n" \
                   f"Wie ben ik, simpele bot die ik ben, om dit tegen te spreken?\n" \
                   f"Daarom speciaal voor jou:"
        pic = "../pictures/vicekapot.png"
        file = discord.File(pic)  # special message for the vice, with a picture too
        embed = discord.Embed()
        embed.set_image(url="attachment://" + pic)
        await channel.send(response, file=file, embed=embed)  # send the built up response to the channel with the file

    @commands.Cog.listener()
    async def on_error(self, error, *args, **kwargs):  # general error handling happens here
        with open('../err.txt', 'a') as f:  # open the error log file
            f.write(f"{str(datetime.now())}\n{str(error)}\n")  # write the date, time and error
            try:  # try to also write the error traceback
                traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
            except Exception as exc:  # if this fails, print the error of this fail instead
                f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
                traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
            f.write("\n\n\n\n\n")  # some whitespace to distinguish different errors
        server = discord.utils.get(self.bot.guilds, id=SERVER)  # find the correct server
        channel = discord.utils.get(server.channels, id=CHANNEL)  # find the correct channel
        await channel.send(f"{const.PROGRAMMER}, er is een fout opgetreden.")  # send error message and mention me

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):  # command error handling happens here
        def write_error():  # function for writing errors to error log
            with open('../err.txt', 'a') as f:  # open the file to append
                f.write(f"{str(ctx.message.created_at)}  {ctx.message.guild}  {ctx.message.channel.category}  "
                        f"{ctx.message.channel}  {ctx.message.author}  {ctx.message.content}\n"
                        f"{ctx.message.jump_url}\n{str(error)}\n")  # write some info on what caused the error
                try:  # try to also write the error traceback
                    traceback.print_exception(etype="ignored", value=error, tb=error.__traceback__, file=f, chain=True)
                except Exception as exc:  # if this fails, print the error of this fail instead
                    f.write("While trying to print the traceback of a Discord error, another exception occurred.\n")
                    traceback.print_exception(etype="ignored", value=exc, tb=exc.__traceback__, file=f, chain=True)
                f.write("\n\n\n\n\n")  # some whitespace to distinguish different errors

        server = discord.utils.get(self.bot.guilds, id=SERVER)  # find the correct server
        channel = discord.utils.get(server.channels, id=CHANNEL)  # find the correct channel
        if isinstance(error, commands.errors.CheckFailure):  # one of the checks failed, someone did something wrong
            # below check failures are pretty self explanatory
            if str(error) == "wrong channel or category":
                await channel.send(f"{ctx.author.mention}\n"
                                   f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention}. "
                                   f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention}. "
                                   f"Dat gaat helaas niet.")
            elif str(error) == "multiline message":
                await channel.send(f"{ctx.author.mention}\n"
                                   f"De DriemanBot accepteert enkel commando's die bestaan uit een enkele lijn.")
            elif str(error) == "wrong nickname input":
                await channel.send(f"De naam die je hebt ingegeven kan niet geaccepteerd worden, kies iets anders.")
            elif str(error) == "player doesn't exist":
                await channel.send(f"Je speelt nog niet mee. Gebruik '{const.PREFIX}{const.MEEDOEN}' om mee te doen.\n"
                                   f"Daarna kan je dit commando pas gebruiken.")
            elif str(error) == "player already exists":
                await channel.send(f"Je speelt al mee. Gebruik '{const.PREFIX}{const.WEGGAAN}' om weg te gaan.\n"
                                   f"Daarna kan je dit commando pas opnieuw gebruiken.")
            elif str(error) == "wrong tempus status":
                await channel.send(f"Je kan enkel '{const.PREFIX}{const.TEMPUS} in' of "
                                   f"'{const.PREFIX}{const.TEMPUS} ex' gebruiken."
                                   f"'{ctx.message.content}' is geen geldig tempus commando.")
            elif str(error) == "not your turn":
                await channel.send("Je bent nu niet aan de beurt, wacht alsjeblieft geduldig je beurt af.\n"
                                   f"Het is nu de beurt aan {self.bot.spel.beurt.name}")
            elif str(error) == "not enough players":
                await channel.send("Nog niet genoeg spelers, "
                                   f"je moet minstens met {MIN_PLAYERS} zijn om te kunnen driemannen (zie art. 1).\n"
                                   f"Wacht tot er nog {MIN_PLAYERS - len(self.bot.spel.players)} speler(s) "
                                   f"meer meedoet/meedoen.")
            elif str(error) == "not enough drink units left":
                await channel.send("Je hebt niet genoeg drankeenheden meer over om uit te delen.")
            elif str(error) == "wrong distribute call":
                await channel.send("Gebruik het juiste format om drankeenheden uit te delen, anders lukt het niet.")
            else:  # in case it isn't one of the above cases, something actually went wrong
                write_error()  # in this case, write the error to the error log and alert me with a mention
                await channel.send(f"{const.PROGRAMMER}, het commando '{ctx.message.content}' heeft iets raar gedaan.")
        elif isinstance(error, commands.errors.CommandNotFound):  # someone entered a non existing command
            if not (ctx.channel.id == CHANNEL and ctx.channel.category.id == CATEGORY):  # in the wrong channel
                await channel.send(f"{ctx.author.mention}\n"
                                   f"De DriemanBot kan enkel gebruikt worden in het kanaal {channel.mention}. "
                                   f"Je probeerde de DriemanBot te gebruiken in het kanaal {ctx.channel.mention}. "
                                   f"Dat gaat helaas niet.")
            else:  # or in the correct one, either way it's not my problem until they make it my problem
                await channel.send(f"{ctx.author.mention}\n"
                                   f"Het commando '{ctx.message.content}' is onbekend. "
                                   "Contacteer de beheerder van de DriemanBot als je denkt dat dit zou moeten werken.")
        elif isinstance(error, commands.errors.MissingRequiredArgument):  # also pretty self explanatory
            response = f"Het commando '{ctx.message.content}' heeft een verplicht argument dat hier ontbreekt."
            if ctx.message.content[:len(const.PREFIX) + len(const.UITDELEN)] == const.PREFIX + const.UITDELEN:
                response += "\nGebruik het juiste format om drankeenheden uit te delen, anders lukt het niet. " \
                            f"Met '{const.PREFIX} help {const.UITDELEN}' kan je zien hoe het moet."
            elif ctx.message.content[:len(const.PREFIX) + len(const.TEMPUS)] == const.PREFIX + const.TEMPUS:
                response += f"\n'{ctx.message.content}' is geen geldig tempus commando."
            await channel.send(response)  # tell them what they did wrong
        else:  # something actually went wrong
            write_error()  # in this case, write the error to the error log and alert me with a mention
            await channel.send(f"{const.PROGRAMMER}, het commando '{ctx.message.content}' is gefaald.")


def setup(bot):
    bot.add_cog(Comms(bot))
