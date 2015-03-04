from collections import namedtuple

from world import *
import poker
import memory

class Bias(object):
    pass


class PokerBias(Bias):
    def __init__(self):
        self.opinions = {}
        self.CardRead = namedtuple('CardRead', ['avg', 'matched', 'flushed', 
                                           'straighted'])

    def read_cards(self, _cards): #FIXME
        cards = sorted(_cards, key=lambda c: c.face)
        avg = 0
        for card in cards[-5]: avg += card.face
        avg /= len(cards[-5])
        flushed = (None, 0)
        for su in 'C', 'D', 'H', 'S':
            count = [c.suit for c in cards].count(su)
            if count > flushed[0]: flushed = suit, count
        matched = 0
        straighted = 0
        run = 0
        last = None
        for card in cards:
            if card.face == last: matches += 1
            elif card.face == last + 1:
                run += 1
                if run > straighted: straighted = run
            elif run > 0: run -= 1
            last = card.face
        return self.CardRead(avg, matched, flushed, straighted)


