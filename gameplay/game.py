#!/usr/bin/env python3
import os  # noqa
import random  # noqa

from dotenv import load_dotenv  # noqa

from .player import Player  # noqa

load_dotenv()
MIN_PLAYERS = int(os.getenv('MIN_TESTERS')) if os.getenv('TESTER') == 'on' else int(os.getenv('MIN_PLAYERS'))
PREFIX = os.getenv('PREFIX')
TEMPUS = os.getenv('TEMPUS')


class Game():
    def __init__(self):
        self.drieman = None
        self.players = []
        self.started = False
        self.beurt = None
        self.dbldriemansetting = False  # TODO: use dbldrieman in hidden bot command

    def add_player(self, player):
        assert isinstance(player, Player), f"Dit is geen speler, maar een {type(player)}."
        assert player.fullname not in [player.fullname for player in self.players], "Deze speler zit al in het spel."
        if self.players:
            player.set_previous_player(self.players[-1])
            self.players[-1].set_next_player(player)
            player.set_next_player(self.players[0])
            self.players[0].set_previous_player(player)
        self.players.append(player)
        return self

    def remove_player(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        if player == self.drieman:
            self.drieman = None
        if self.beurt == player:
            self.beurt = player.next_player
        player.next_player.set_previous_player(player.previous_player)
        player.previous_player.set_next_player(player.next_player)
        self.players.remove(player)
        response = ""
        if player.achterstand != 0:
            response += f"{player.name}, je hoort nog {player.achterstand} drankeenheden te drinken.\n"
            player.drinking()
        response += f"{player.name} heeft in totaal {player.totaal} drankeenheden gedronken.\n" \
                    f"{player.name} heeft het spel verlaten. Slaap zacht kameraad."
        return response

    def start_game(self):
        if len(self.players) >= MIN_PLAYERS:
            self.started = True
            self.beurt = self.players[0]
            response = "Het spel is gestart."
        else:
            response = "Nog niet genoeg spelers, " \
                       f"je moet minstens met {MIN_PLAYERS} zijn om te kunnen driemannen (zie art. 1).\n" \
                       f"Wacht tot er nog {MIN_PLAYERS - len(self.players)} speler(s) meer meedoet/meedoen."
        return response

    def player_tempus(self, player, status):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(status, str) and status in ["in", "ex"], \
            f"Misbruik van {TEMPUS} commando, verkeerde status {status}."  # normaal gezien gecheckt voor de functiecall
        names = [player.fullname for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        if (status, player.tempus) in [("ex", True), ("in", False)]:
            player.switch_tempus()
            if player.tempus:
                response = f"{player.name} heeft nu tempus, tot zo!"
            else:
                response = f"Welkom terug {player.name}, je moet nu {player.achterstand} drankeenheden drinken."
                player.drinking()
        else:
            response = f"Je bent al in de modus '{TEMPUS} {status}'."
        return response

    def roll(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        assert player == self.beurt, \
            "Een speler die niet aan de beurt is heeft geworpen."  # normaal gezien gecheckt voor de functiecall
        if player.tempus:
            return f"Je bent nog in modus '{TEMPUS} in'. Gebruik '{PREFIX}{TEMPUS} ex' om verder te spelen."
        dice = [random.randint(1, 6) for _ in range(2)]
        response = f"{player.name} gooide een {dice[0]} en een {dice[1]}.\n"
        if 3 in dice:
            if self.drieman is not None:
                self.drieman.add_to_drink(dice.count(3) * (self.drieman.dbldrieman if self.dbldriemansetting else 1))
        if sum(dice) == 3:
            if self.drieman.dbldrieman == 2:
                self.drieman.switch_dbldrieman()
            if self.drieman == player:
                player.switch_dbldrieman()
            self.drieman = player
            response += f"{player.name} is nu drieman.\n"
        elif sum(dice) == 6:
            player.previous_player.add_to_drink(1)
        elif sum(dice) == 7:
            player.add_to_drink(1)
        elif sum(dice) == 8:
            player.next_player.add_to_drink(1)
        if dice[0] == dice[1]:
            player.uitdelen += dice[0]
        if not (sum(dice) in range(6, 8 + 1) or dice[0] == dice[1]):
            self.beurt = self.beurt.next_player
        response += self.drink()
        return response

    def drink(self):
        response = ""
        for player in self.players:
            assert player.achterstand >= 0, "Het spel is kapot, iemand heeft een negatief aantal te drinken eenheden."
            if player.achterstand > 0:
                if player.tempus:
                    response += f"{player.name} is een tempus aan het nemen en " \
                                f"staat momenteel {player.achterstand} drankeenheden achter.\n"
                else:
                    response += f"{player.name} moet {player.achterstand} drankeenheden drinken.\n"
                    player.drinking()
            if player.uitdelen > 0:
                response += f"{player.name} mag (in totaal) nog {player.uitdelen} drankeenheden uitdelen.\n"
        response += "Dat is alles, drinken maar!"
        return response

    def check_player_distributor(self, player, units, zero_allowed):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.fullname for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        return player.uitdelen <= units and (player.uitdelen > 0 or zero_allowed)

    def distributor(self, player, other_player, units):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(other_player, int), f"Dit is geen nummer van een speler, maar een {type(other_player)}."
        assert isinstance(units, int), f"Dit is geen aantal drankeenheden, maar een {type(units)}."
        names = [player.fullname for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        assert other_player in range(
            len(self.players)), "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        other_player = self.players[other_player]
        player.distribute(other_player, units)
        return self

    def switch_dbldrieman_setting(self):
        self.dbldriemansetting = not self.dbldriemansetting
        return self
