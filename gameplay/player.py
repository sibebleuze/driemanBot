#!/usr/bin/env python3

class Player():
    def __init__(self, discorduser):
        self.fullname = str(discorduser)  # TODO: verder uitwerken fullname
        self.name = discorduser.mention
        self.nickname = discorduser.display_name
        self.previous_player = self
        self.next_player = self
        self.tempus = False
        self.achterstand = 0
        self.totaal = 0
        self.uitdelen = 0

    def set_previous_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.previous_player = player
        return self

    def set_next_player(self, player):
        assert type(player) == Player, f"Dit is geen speler, maar een {type(player)}."
        self.next_player = player
        return self

    def switch_tempus(self):
        """
        This is the only method in Player that doesn't return itself, i.e. a Player object.
        Be careful with this!
        """
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
        return self

    def drinking(self):
        self.achterstand = 0
        return self

    def distribute(self, player, units):
        assert self.uitdelen >= units, \
            "Niet genoeg drankeenheden over om uit te delen"  # normaal gecheckt voor functiecall
        player.achterstand += units
        self.uitdelen -= units
        return self

    def get_distribute(self, units):
        assert self.uitdelen >= 0, "Het spel is kapot, iemand heeft een negatief aantal uit te delen eenheden."
        self.uitdelen += units
        return self

    def set_nickname(self, nickname):
        if nickname is not None:
            self.nickname = nickname
        return self
