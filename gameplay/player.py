#!/usr/bin/env python3

class Player():
    """All Player methods return self to allow chaining commands if that is ever required."""

    def __init__(self, discorduser):
        self.fullname = str(discorduser)  # unique string to identify players
        mention = discorduser.mention.replace('@!', '@')  # some players have a ! in their mention, some don't
        self.name = mention  # string usable by bot to mention players by their Discord name
        self.nickname = discorduser.display_name[:50]  # player nickname, defaults to Discord display name (max len 50)
        self.previous_player = self  # we have no info on other players at this point,
        self.next_player = self  # so we set these to the only player we do know, which is self
        self.tempus = False  # at initiation, the player is not taking a tempus
        self.achterstand = 0  # at initiation, the player has no unfinished drinks
        self.totaal = 0  # in fact, at initiation, the player has no drinks at all
        self.uitdelen = 0  # at initiation, the player cannot assign drinks to other players
        self.dbldrieman = 1  # at initiation, the player is not a dubbeldrieman
        self.driemannumber = 0  # at initiation, the player has not been drieman

    def set_previous_player(self, player):
        assert isinstance(player, Player), f"Dit is geen speler, maar een {type(player)}."
        self.previous_player = player  # change the player whose turn is just before yours
        return self

    def set_next_player(self, player):
        assert isinstance(player, Player), f"Dit is geen speler, maar een {type(player)}."
        self.next_player = player  # change the player whose turn is just after yours
        return self

    def switch_tempus(self):
        self.tempus = not self.tempus  # take a break or come back from one
        return self

    def add_to_drink(self, units):  # keep track of how many drinks one should drink
        self.achterstand += units  # this value will be used to print the amount of drink during playtime
        self.totaal += units  # this value will be printed when a player leaves
        return self

    def drinking(self):
        self.achterstand = 0  # reset playtime drink count when round is over or one returns from tempus
        return self

    def distribute(self, player, units):
        assert self.uitdelen >= units, \
            "Niet genoeg drankeenheden over om uit te delen"  # should be checked before function call
        player.add_to_drink(units)  # assign drinking units to another player
        self.uitdelen -= units  # substract assigned units from your assignable units
        return self

    def get_distribute(self, units):
        assert self.uitdelen >= 0, "Het spel is kapot, iemand heeft een negatief aantal uit te delen eenheden."
        self.uitdelen += units  # get some units assigned that you can later distribute between other players
        return self

    def set_nickname(self, nickname):
        if nickname is not None:  # this is sometimes indeed called upon with None, so that's filtered out here
            self.nickname = nickname  # set the nickname to something else than the default one
        return self

    def switch_dbldrieman(self):
        self.dbldrieman = {1: 2, 2: 1}[self.dbldrieman]  # switch a player to dubbeldrieman or back to normal drieman
        return self
