from world import *


class Episode(object):
    def __init__(self):
        self.scene = scene # class
        self.actions = {} # action: priority?
        self.options = {} # action: {'salience': 0, 'outcome': None}
        self.emotion = {'peak': None, 'end': None, 'average': None}
        self.goals = {} # Goal objects with weight value
        self.sequence = {'start': None, 'end': None, 'prev': None, 'next': None}
        self.date = {'occurrence': 0, 'last recall': 0, 'total recalls': 0}

# This could be any action, potential or memory
class Action(object):
    def __init__(self):
        self.description = None
        self.cause = None # Episode
        self.effect = None # Episode
        self.emotion = None # ??
        self.evaluation = None

class PokerEpisode(Episode):
    def __init__(self, player, game):
        self.pos = game.players.index(player)
        self.outcome = None
        self.hand = [card.compress() for card in player.hand]
        self.moves = []

class PokerEpisode(Episode): #FIXME
    def __init__(self, game):
        self.players = [] # ordered for first round, then offset
        self.real_chip_total = 0 # otherwise % are used
        for player in game.players:
            self.players.append(player.actor)
            self.real_chip_total += player.bank
        self.location = game.location
        self.rounds = [] # list of lists of phases
        self.winner = None
        self.hierarchy = ['High card', 'Pair', 'Two pairs', 'Three of a kind', 
                          'Flush', 'Straight', 'Full house', 'Four of a kind',
                          'Straight flush']

    def dump(self):
        for rnd in self.rounds:
            print("****\nRound {}:".format(self.rounds.index(rnd)))
            for phase in rnd['phases']:
                print("Phase {}".format(rnd['phases'].index(phase)))
                print(phase)
            for actor in rnd['outcome']:
                print("{} outcome: {}".format(actor.name, 
                                              rnd['outcome'][actor]))
        print("Players: {}\nWinner: {}".format(self.players, self.winner))

    def retrieve(self, cues, bias=None):
        # check trick for +/- chance
        opinion = 0
        sources = 0
        print("Call retrieve with {}".format(cues['trick']))
        try: trick = self.hierarchy.index(cues['trick'])
        except ValueError: trick = None

        for ep in self.rounds:
            for actor in ep['outcome']:
                if actor.name == "Daedalus": continue
                comp = 2
                if trick is not None:
                    try: 
                        other = self.hierarchy.index(
                            ep['outcome'][actor]['trick'])
                        if other == trick: comp = 4
                        else: comp = 1
                        print("MATCH {}: {}".format(trick, comp))
                    except KeyError: pass #print("No trick")
                try:
                    comp -= self.get_comparison(cues['read'], 
                                            ep['outcome'][actor]['read'])
                except KeyError: print("No read")
                if comp <= 0: continue
                if ep['outcome'][actor]['chips'] > 0: opinion += comp
                else: opinion -= comp
                #opinion += comp * ep['outcome'][actor]['chips']
                sources += 1
        #print("OPINION: {} for trick {}".format(opinion, str(trick)))
        if sources > 1: opinion /= sources
        return opinion

    def get_comparison(self, this, that):
        comp = 0
        for x, y in zip(this, that):
            print(x, y)
            comp += abs(x - y)
        print("COMP: {} for {} + {}".format(comp, this,that))
        return comp

    def consolidate(self):
        kept, removed, whole, orig = 0, 0, 0, len(self.rounds)
        kill = []
        for rnd in self.rounds:
            for actor in list(rnd['outcome'].keys()):
                if abs(rnd['outcome'][actor]['chips']) < 0.08:
                    del rnd['outcome'][actor]
                    removed += 1
                else: kept += 1
            if rnd['outcome'] == {}:
                kill.append(rnd)
                whole += 1
        for victim in kill: self.rounds.remove(victim)

        print("Consolidation: {} kept / {} removed ({} / {})".format(kept, 
                                                removed, whole, orig))


#class Scene(object):
#    def __init__(self):
#        pass


#class Form(object):
#    def __init__(self):
#        pass

# a character or something than can make actions
#class Actor(Form):
#    def __init__(self):
#        super(Actor, self).__init__()

# a world item, like a table
#class Static(Form):
#    def __init__(self):
#        super(Static, self).__init__()

# a world background, like sky or mountain range, something general
#class Background(Form):
#    def __init__(self):
#        super(Background, self).__init__()
