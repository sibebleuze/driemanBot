#!/usr/bin/env python3
from player import Player  # noqa


class Game():
    def __init__(self):
        self.drieman = None
        self.players = []
        self.started = False

    def add_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        assert player not in self.players, "Deze speler zit al in het spel."
        if self.players:
            player.set_previous_player(self.players[-1])
            self.players[-1].set_next_player(player)
            player.set_next_player(self.players[0])
            self.players[0].set_previous_player(player)
        self.players.append(player)

    def remove_player(self, player):
        assert type(player) == str, f"Dit is geen naam van een speler, maar een {type(player)}."
        names = [player.name for player in self.players]
        assert player in names, "Deze speler zit niet in het spel."  # normaal gezien gecheckt voor de functiecall
        player = self.players[names.index(player)]
        player.next_player.set_previous_player(player.previous_player)
        player.previous_player.set_next_player(player.next_player)
        self.players.remove(player)
        return f"Speler {player.name} heeft het opgegeven. Slaap zacht jonge vriend."

    def start_game(self):
        if len(self.players) >= 4:
            self.started = True
            return "Het spel is gestart."
        else:
            return "Nog niet genoeg spelers, je moet minstens met vier zijn om te kunnen driemannen (zie art. 1).\n" \
                   f"Wacht tot er nog {4 - len(self.players)} speler(s) meer meedoet/meedoen."
