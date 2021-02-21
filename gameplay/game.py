#!/usr/bin/env python3
import os  # noqa

import discord  # noqa
import numpy as np  # noqa

import gameplay.constants as const  # noqa
import gameplay.player as pl  # noqa

# minimum amount of players is lowered when testing new code
MIN_PLAYERS = const.MIN_TESTERS if const.TESTER else const.MIN_PLAYERS


class Game():
    def __init__(self):
        self.drieman = None  # no one is drieman at the start of the game
        self.players = []  # keep a list of all players that are in the game
        self.beurt = None  # it is no ones turn yet
        self.dbldriemansetting = False  # a new game is started without the dubbeldriemansetting on

    def add_player(self, player):
        assert isinstance(player, pl.Player), f"Dit is geen speler, maar een {type(player)}."
        assert player.fullname not in [player.fullname for player in self.players], "Deze speler zit al in het spel."
        if self.players:  # if there are already players in the game, a new player needs to be squeezed in between
            player.set_previous_player(self.players[-1])  # the new player has his turn after the player that
            self.players[-1].set_next_player(player)  # joined last, this change needs to be defined for both players
            player.set_next_player(self.players[0])  # the new player has his turn right before the player that joined
            self.players[0].set_previous_player(player)  # first, this change needs to be defined for both players
        self.players.append(player)  # finally, the new player is added at the end of the list of players in the game
        return self

    def remove_player(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]  # generate a list with the full names of players, in order
        assert player in names, "Deze speler zit niet in het spel."  # should be checked before function call
        player = self.players[names.index(player)]  # find the correct Player in the list of active players
        if player == self.drieman:  # if the drieman leaves, drieman returns to its default value of None
            self.drieman = None
        if self.beurt == player:  # if it is this players turn, the turn goes to the next player
            self.beurt = player.next_player
        player.next_player.set_previous_player(player.previous_player)  # next and previous player are connected
        player.previous_player.set_next_player(player.next_player)
        self.players.remove(player)  # player is removed from the active player list
        while self.beurt.tempus and not all([p.tempus for p in self.players]):
            self.beurt = self.beurt.next_player
        response = ""  # a response is built up for the bot to send to the channel for the player leaving
        if player.achterstand != 0:  # if a player has drinking units left on his tab, this is printed out
            response += f"{player.name}, je hoort nog {player.achterstand} drankeenheden te drinken.\n"
            player.drinking()  # he then has no drinking units left
        response += f"{player.name} heeft in totaal {player.totaal} drankeenheden gedronken.\n" \
                    f"{player.name} heeft het spel verlaten. Slaap zacht kameraad."  # goodbye message
        return response  # total message is returned to the bot for sending

    def player_tempus(self, player, status):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(status, str) and status in ["in", "ex"], \
            f"Misbruik van {const.TEMPUS} commando, verkeerde status {status}."  # normaal gezien vooraf gecheckt
        names = [player.fullname for player in self.players]  # generate a list with the full names of players, in order
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]  # find the correct Player in the list of active players
        if (status, player.tempus) in [("ex", True), ("in", False)]:  # if a player isn't already in the desired state
            player.switch_tempus()  # switch the players tempus state
            while self.beurt.tempus and not all([p.tempus for p in self.players]):  # if the player on turn is on
                self.beurt = self.beurt.next_player  # tempus, give turn to next player if there are any left
            if player.tempus:  # define a message addressing the player for the bot to send
                response = f"{player.name} heeft nu tempus, tot zo!"
            else:
                response = f"Welkom terug {player.name}, je moet nu {player.achterstand} drankeenheden drinken."
                player.drinking()  # after telling the player how much to drink, forget that amount
        else:
            response = f"Je bent al in de modus '{const.TEMPUS} {status}'."  # tell player he already has what he wants
        return response  # total message is returned to the bot for sending

    def roll(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]  # generate a list with the full names of players, in order
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]  # find the correct Player in the list of active players
        assert player == self.beurt, \
            "Een speler die niet aan de beurt is heeft geworpen."  # normaal gezien gecheckt voor de functiecall
        url = None  # in some cases, a file is being sent with the message here, the name of the file will be in url
        if player.tempus:  # if the player is in tempus mode, he cannot roll the dice
            response = f"Je bent nog in modus '{const.TEMPUS} in'. " \
                       f"Gebruik '{const.PREFIX}{const.TEMPUS} ex' om verder te spelen."
        else:  # the player can roll the dice here and a succession of events is calculated
            dice = list(np.random.randint(1, 6, 2))  # draw two random numbers between 1 and 6, borders included
            response = f"{player.name} gooide een {dice[0]} en een {dice[1]}.\n"
            if 3 in dice and self.drieman is not None:  # the drieman drinks one unit per 3 on the dice
                self.drieman.add_to_drink(dice.count(3) * self.drieman.dbldrieman)  # or two if he is dubbeldrieman
            if sum(dice) == 3:  # a player becomes drieman if the dice sum up to three
                if self.drieman and self.drieman.dbldrieman == 2:  # if the previous drieman was dubbeldrieman,
                    self.drieman.switch_dbldrieman()  # it is no longer the case
                if self.dbldriemansetting and self.drieman and self.drieman == player:  # if the dubbeldrieman setting
                    player.switch_dbldrieman()  # is on, the drieman who rolls another total 3 is now dubbeldrieman
                self.drieman = player  # the drieman is actually set to the new drieman here
                if self.dbldriemansetting and self.drieman.dbldrieman == 2:  # if we do have a new dubbeldrieman,
                    url = "../pictures/dubbeldrieman.jpg"  # use this picture
                    response += f"{self.drieman.name} is nu dubbeldrieman.\n"  # and use this line to tell everyone
                else:  # if we just have a new drieman
                    url = "../pictures/drieman.png"  # use this picture instead
                    response += f"{self.drieman.name} is nu drieman.\n"  # and this line to tell everyone
            elif sum(dice) == 6:  # if the dice sum to 6, the previous player drinks one unit
                player.previous_player.add_to_drink(1)
            elif sum(dice) == 7:  # if the dice sum to 7, the current player drinks one unit
                player.add_to_drink(1)
            elif sum(dice) == 8:  # if the dice sum to 8, the next player drinks one unit
                player.next_player.add_to_drink(1)
            if dice[0] == dice[1]:  # if the dice are equal, the player gets to assign drink units,
                player.uitdelen += dice[0]  # as many as one dice counts
            if not (sum(dice) in range(6, 8 + 1) or dice[0] == dice[1]):  # if nothing happens (except for 3s)
                self.beurt = self.beurt.next_player  # the turn goes to the next person
                while self.beurt.tempus and not all([p.tempus for p in self.players]):
                    self.beurt = self.beurt.next_player
            response += self.drink()  # this function builds additional text to tell everyone how much to drink
        response += f"\n{self.beurt.name} is aan de beurt."
        return response, url  # the response and the url are returned to the bot

    def drink(self):
        response = ""
        for player in self.players:  # figure out for all players how much they must drink
            assert player.achterstand >= 0, "Het spel is kapot, iemand heeft een negatief aantal te drinken eenheden."
            if player.achterstand > 0:  # if they have a non-zero amount of units to drink left, start building response
                if player.tempus:  # keep the count if they are taking a tempus
                    response += f"{player.name} is een tempus aan het nemen en " \
                                f"staat momenteel {player.achterstand} drankeenheden achter.\n"
                else:  # print out the count and forget it
                    response += f"{player.name} moet {player.achterstand} drankeenheden drinken.\n"
                    player.drinking()
            if player == self.beurt and player.uitdelen > 0:  # also print how much they can hand out if it's their turn
                response += f"{player.name} mag (in totaal) nog {player.uitdelen} drankeenheden uitdelen.\n"
        response += "Dat is alles, drinken maar!"  # print a final sentence to not let the statement end with newline
        return response  # total message is returned to the bot for sending

    def check_player_distributor(self, player, units, zero_allowed):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]  # generate a list with the full names of players, in order
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]  # find the correct Player in the list of active players
        return player.uitdelen >= units and (player.uitdelen > 0 or zero_allowed)  # determine if they do what they want

    def distributor(self, player, other_player, units):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(other_player, int), f"Dit is geen nummer van een speler, maar een {type(other_player)}."
        assert isinstance(units, int), f"Dit is geen aantal drankeenheden, maar een {type(units)}."
        names = [player.fullname for player in self.players]  # generate a list with the full names of players, in order
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        assert other_player in range(
            len(self.players)), "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]  # find the correct Player in the list of active players
        other_player = self.players[other_player]  # select other Player by using position in active players list
        player.distribute(other_player, units)  # let the player distribute the units to the other player
        return self  # this could be chained if desired

    def switch_dbldrieman_setting(self):
        self.dbldriemansetting = not self.dbldriemansetting  # switch the dubbeldrieman setting
        return self  # this could be chained if desired
