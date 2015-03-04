from collections import namedtuple

class Actor(object):
    def __init__(self, name):
        self.name = name
        self.loc = {}
        self.desc = []
        self.inv = []
        self.equipped = []
        self.memory = [] # hack
        self.poker_wins = 0

    def create_memory(self, typeof, mem):
        self.memory.append(mem)


class Static(object):
    def __init__(self):
        self.loc = {}
        self.name = None
        self.desc = []

class Cell(object):
    def __init__(self):
        self.name = None
        self.desc = []
        self.inv = []


class PokerRoom(Cell):
    def __init__(self):
        super(PokerRoom, self).__init__()
        self.name = 'The poker room'
        self.info = 'warm and cosy room for playing poker in. Jazz music plays.'


# Statics

class Table(Static):
    def __init__(self):
        super(Table, self).__init__()
        self.name = 'table'
        self.info = 'a table'

class PlayingCard(Static):
    def __init__(self, suit, face):
        super(PlayingCard, self).__init__()
        self.suit = {'C': "Clubs", 'D': "Diamonds", 'H': "Hearts", 
                     'S': "Spades", 'U': "Unknown"}[str(suit).upper()[0]]
        if type(face) is not Unknown: self.face = int(face)
        else: self.face = face
        self.name = self._get_name(self.suit, self.face)
        self.info = 'a playing card'

    # Init the pretty name of the card
    def _get_name(self, suit, face):
        if type(face) is not Unknown and face > 10:
            face = {11: 'Jack', 12: 'Queen', 13: 'King',
                    14: 'Ace'}[face]
        return "{} of {}".format(face, suit)
    
    def compress(self):
        if type(self.face) is Unknown: face = 'U'
        else: face = self.face
        if type(self.suit) is Unknown: suit = 'U'
        else: suit = self.suit[0]
        Card = namedtuple('Card', ['face', 'suit'])
        return Card(face, suit)

    def compare(self, other):
        if type(other) is str:
            face, suit = other.split()
            if face == 'U': face = Unknown
            else: face = int(face)
            if suit == 'U': suit = Unknown
        else: #if type(other) is PlayingCard:
            face = other.face
            suit = other.suit
        #else:
        #    raise ValueError("Can't compare {} with PlayingCard".format(other))
        comp = 0
        if self.suit[0] == suit[0]:
            if self.face == face: return 100
            else: comp += 25
        else: comp -= 25
        diff = abs(self.face - face)
        if diff < 5: comp += 75 // 1 + pow(diff, 2)
        return comp
    
    def __int__(self):
        return int(self.face)

    def __str__(self):
        return self.name
    '''
    def __gt__(self, card):
        return int(self) > int(card)

    def __lt__(self, card):
        return int(self) < int(card)

    def __ge__(self, card):
        return int(self) >= int(card)

    def __le__(self, card):
        return int(self) <= int(card)

    def __eq__(self, card):
        if type(card) is PlayingCard:
            if self.face == card.face and self.suit == card.suit:
                return True
            else: return False
        else:
            raise TypeError("Not sane comparison: " + self + card)

    def __ne__(self, card):
        if type(card) is PlayingCard:
            if self == card: return False
            else: return True
        else: 
            raise TypeError("Not sane comparison: " + self + card)

    def __hash__(self):
        return id(self)
    '''

class Unknown(object):
    def __init__(self, mini=None, maxi=None):
        self.mini = mini
        self.maxi = maxi
        self.xposs = None # exclusive possibilities
        self.poss = None # non-exclusive poss

    def __str__(self):
        return 'Unknown'

    def __bool__(self):
        return False

    def __int__(self):
        #return self
        raise UnknownError("Unknown can not be represented as an int")

    def __lt__(self, x):
        if self.mini is not None:
            if self.mini > x:
                return False
        if self.maxi is not None:
            if self.maxi < x:
                return True
        return self

    def __gt__(self, x):
        if self.mini is not None:
            if self.mini > x:
                return True
        if self.maxi is not None:
            if self.maxi < x:
                return False
        return self

    def __le__(self, x):
        if self.mini is not None:
            if self.mini > x:
                return False
        if self.maxi is not None:
            if self.maxi <= x:
                return True
        return self

    def __ge__(self, x):
        if self.mini is not None:
            if self.mini >= x:
                return True
        if self.maxi is not None:
            if self.maxi < x:
                return False
        return self
        
    def __eq__(self, x):
        if (self < x) is True: return False
        if (self > x) is True: return False
        return self

    def __ne__(self, x):
        if (self < x) is True: return True
        if (self > x) is True: return True
        return self

class UnknownError(Exception):
    pass

class PokerBank(Static):
    def __init__(self, value):
        super(PokerBank, self).__init__()
        self.value = value
        self.name = 'poker chips'
