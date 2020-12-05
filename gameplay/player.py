#!/usr/bin/env python3

class Player():
    def __init__(self, name):
        self.name = name
        self.previous_player = self
        self.next_player = self
        self.tempus = False
        self.achterstand = 0
        self.total = 0
        self.uitdelen = 0

    def set_previous_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.previous_player = player

    def set_next_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.next_player = player

    def switch_tempus(self):
        self.tempus = not self.tempus
