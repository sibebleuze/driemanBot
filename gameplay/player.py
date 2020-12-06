#!/usr/bin/env python3

class Player():
    def __init__(self, name, nickname=None):
        self.name = name
        self.nickname = nickname
        self.previous_player = self
        self.next_player = self
        self.tempus = False
        self.achterstand = 0
        self.totaal = 0
        self.uitdelen = 0

    def set_previous_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.previous_player = player

    def set_next_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.next_player = player

    def switch_tempus(self):
        self.tempus = not self.tempus
        if self.tempus:
            response = f"{self.name} heeft nu tempus, tot zo!"
        else:
            response = f"Welkom terug {self.name}, je moet nu {self.achterstand} drankeenheden drinken."
            self.drinking()
        return response

    def add_to_drink(self, units):
        self.achterstand += units
        self.totaal += units

    def drinking(self):
        self.achterstand = 0

    def distribute(self, player, units):
        assert self.uitdelen >= units, \
            "Niet genoeg drankeenheden over om uit te delen"  # normaal gecheckt voor functiecall
        player.acherstand += units
        self.uitdelen -= units

    def get_distribute(self, units):
        assert self.uitdelen >= 0, "Het spel is kapot, iemand heeft een negatief aantal uit te delen eenheden."
        self.uitdelen += units
