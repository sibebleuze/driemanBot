# discord doesn't know enough numbers in emojis to make this idea work
# i tried to make all commands available with an emoji, but got stuck on const.UITDELEN since i need numbers > 10

GAME_DIE = b'\xF0\x9F\x8E\xB2'.decode('utf-8')
CLINKING_BEERS = b'\xF0\x9F\x8D\xBB'.decode('utf-8')
_NUMBERS = {1: b'\xE2\x91\xA0', 2: b'\xE2\x91\xA1', 3: b'\xE2\x91\xA2', 4: b'\xE2\x91\xA3', 5: b'\xE2\x91\xA4',
            6: b'\xE2\x91\xA5', 7: b'\xE2\x91\xA6', 8: b'\xE2\x91\xA7', 9: b'\xE2\x91\xA8', 10: b'\xE2\x91\xA9',
            11: b'\xE2\x91\xAA', 12: b'\xE2\x91\xAB', 13: b'\xE2\x91\xAC', 14: b'\xE2\x91\xAD', 15: b'\xE2\x91\xAE',
            16: b'\xE2\x91\xAF', 17: b'\xE2\x91\xB0', 18: b'\xE2\x91\xB1', 19: b'\xE2\x91\xB2', 20: b'\xE2\x91\xB3',
            21: b'\xE3\x89\x91', 22: b'\xE3\x89\x92', 23: b'\xE3\x89\x93', 24: b'\xE3\x89\x94', 25: b'\xE3\x89\x95',
            26: b'\xE3\x89\x96', 27: b'\xE3\x89\x97', 28: b'\xE3\x89\x98', 29: b'\xE3\x89\x99', 30: b'\xE3\x89\x9A'}
NUMBERS = {key: value.decode('utf-8') for key, value in _NUMBERS.items()}
EMOJIS = {value: key for key, value in NUMBERS.items()}
