#!/usr/bin/env python3
import os  # noqa
import random  # noqa

from dotenv import load_dotenv  # noqa

from .player import Player  # noqa

load_dotenv()
MIN_PLAYERS = int(os.getenv('MIN_TESTERS')) if os.getenv('TESTER') == 'on' else int(os.getenv('MIN_PLAYERS'))
TEMPUS = os.getenv('TEMPUS')


class Game():
    def __init__(self):
        self.drieman = None
        self.players = []
        self.started = False
        self.beurt = None

    def add_player(self, player):
        assert isinstance(player, Player), f"Dit is geen speler, maar een {type(player)}."
        assert player not in self.players, "Deze speler zit al in het spel."
        if self.players:
            player.set_previous_player(self.players[-1])
            self.players[-1].set_next_player(player)
            player.set_next_player(self.players[0])
            self.players[0].set_previous_player(player)
        self.players.append(player)

    def remove_player(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        if player == self.drieman:
            self.drieman = None
        player.next_player.set_previous_player(player.previous_player)
        player.previous_player.set_next_player(player.next_player)
        self.players.remove(player)
        # TO DO: meegeven hoeveel drankeenheden nog gedronken moeten worden (als deze persoon tempus heeft bvb.)
        return f"Speler {player.name} heeft het opgegeven. Slaap zacht jonge vriend."

    def start_game(self):
        if len(self.players) >= MIN_PLAYERS:
            self.started = True
            self.beurt = self.players[0]
            return "Het spel is gestart."
        else:
            return "Nog niet genoeg spelers, " \
                   f"je moet minstens met {MIN_PLAYERS} zijn om te kunnen driemannen (zie art. 1).\n" \
                   f"Wacht tot er nog {MIN_PLAYERS - len(self.players)} speler(s) meer meedoet/meedoen."

    def player_tempus(self, player, status):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(status, str) and status in ["in", "ex"], \
            f"Misbruik van {TEMPUS} commando, verkeerde status {status}."  # normaal gezien gecheckt voor de functiecall
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        if (status, player.tempus) in [("ex", True), ("in", False)]:
            player.switch_tempus()
            return f"{player.name} heeft nu tempus, tot zo!" if player.tempus \
                else f"Welkom terug {player.name}, je staat nog {player.achterstand} drankeenheden achter."
        else:
            return f"Je bent al in de modus '{TEMPUS} {status}'."

    def roll(self, player):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        assert player == self.beurt, \
            "Een speler die niet aan de beurt is heeft geworpen."  # normaal gezien gecheckt voor de functiecall
        dice = [random.randint(1, 6) for _ in range(2)]
        if 3 in dice:
            if self.drieman is not None:
                self.drieman.achterstand += dice.count(3)
        if sum(dice) == 3:
            self.drieman = player
        elif sum(dice) == 6:
            player.previous_player.achterstand += 1
        elif sum(dice) == 7:
            player.achterstand += 1
        elif sum(dice) == 8:
            player.next_player.achterstand += 1
        elif dice[0] == dice[1]:
            player.uitdelen += dice[0]
        if not (sum(dice) in range(6, 8 + 1) or dice[0] == dice[1]):
            self.beurt = self.beurt.next_player
        response = f"{player.name} gooide een {dice[0]} en een {dice[1]}.\n"
        response += self.drink()
        return response

    def drink(self):
        # TO DO: bepaal wie er allemaal moet drinken en hoeveel drankeenheden
        return "NotImplementedError"

    def check_player_distributor(self, player, units):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        return 0 < player.uitdelen <= units

    def distributor(self, player, other_player, units):
        assert isinstance(player, str), f"Dit is geen naam van een speler, maar een {type(player)}."
        assert isinstance(other_player, int), f"Dit is geen nummer van een speler, maar een {type(other_player)}."
        assert isinstance(units, int), f"Dit is geen aantal drankeenheden, maar een {type(units)}."
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        assert other_player in range(
            len(self.players)), "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        other_player = self.players[other_player]
        player.distribute(other_player, units)
        return True
