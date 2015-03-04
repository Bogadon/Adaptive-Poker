
import random
from time import sleep
from collections import namedtuple

from world import * #...
from memory import *

# cards are of form '2 C' -> '14 S' : 2 of clubs to Ace of Spades
global ACE, KING, QUEEN, JACK
ACE, KING, QUEEN, JACK = 14, 13, 12, 11

class PokerPlayer(object):
    def __init__(self, actor, bank, game):
        self.actor = actor
        self.name = actor.name
        self.bank = bank
        self.hand = []
        self.bet = 0
        self.is_folded = False
        self.is_all_in = False
        self.is_out = False
        self.round_winnings = None
        self.is_showing = False
        self.game = game
        self.actor.poker_type = type(self)
        self.CardRead = namedtuple('CardRead', ['trick', 'high', 'avg', 
                                        'matched', 'flushed', 'straighted'])

    def get_move(self, moves):
        raise NotImplementedError

    def notify(self, event, detail=None):
        pass

    def read_cards(self, _cards):
        cards = sorted(_cards, key=lambda c: c.face)
        trick = self.game.find_best_hand(cards)['trick']
        trick = self.game.hierarchy.index(trick)
        high = cards[-1].face
        avg = 0
        for card in cards[-5:]: avg += card.face
        avg /= len(cards[-5:])
        flushed = 0
        for su in 'C', 'D', 'H', 'S':
            count = len([True for c in cards if c.suit[0] == su])
            if count > flushed: flushed = count
        matched = 0
        straighted = 0
        run = 0
        last = 0
        for card in cards:
            if card.face == last: matched += 1
            elif card.face == last + 1:
                run += 1
                if run > straighted: straighted = run
            elif run > 0: run -= 1
            last = card.face
        # normalise
        avg /= 14
        high /= 14 # ACE
        if flushed >= 5: flushed = 1
        else: flushed /= len(cards)
        if straighted >= 5: straighted = 1
        else: straighted /= len(cards)
        matched /= len(cards)
        return self.CardRead(trick, high, avg, matched, flushed, straighted)

class HumanPokerPlayer(PokerPlayer):
    #def __init__(self, actor, bank, game):
    #    super(HumanPokerPlayer, self).__init__(actor, bank, game)

    def get_move(self, moves):
        while True:
            key = 1
            for move in moves:
                print("%d) %s" %(key, move))
                key += 1
            try: return moves[int(input("Choice: ")) - 1]
            except ValueError: print("Invalid, please enter an int")
            except IndexError: print("Invalid, outside range")

class AIRandomPoker(PokerPlayer):

    def get_move(self, moves):
        print("{}'s turn...".format(self.name))
        #sleep(1)
        move = random.choice(moves)
        #print("%s: %s" %(self.name, move))
        return move


class AIConstantPoker(PokerPlayer):
    def __init__(self, actor, bank, game, logic=None):
        super(AIConstantPoker, self).__init__(actor, bank, game)
        if logic is None:
            self.logic = 2 #random.randint(0, 5)
        else:
            self.logic = logic

    def get_move(self, moves):
        print("{}'s turn...".format(self.name))
        #sleep(1)
        opt = self.logic
        while True:
            try: return moves[opt]
            except IndexError: opt -= 1

class AIReactivePoker(PokerPlayer):
    def get_move(self, moves):
        cards = self.hand[:]
        cards += self.game.comm_cards
        trick = self.game.find_best_hand(cards)
        try: opt = self.game.hierarchy.index(trick['trick'])
        except ValueError: opt = 0
        if opt == 0: # fold
            if "+0" in moves[1]:
                opt = 1
            elif self.game.phase < 2:
                if self.read_cards(self.hand).high > 10:
                    opt = 1
        while True:
            try: return moves[opt]
            except IndexError: opt -= 1

class AIPokerPlayer(PokerPlayer):
    def __init__(self):
        raise NotImplementedError
    def get_move(self, moves):
        raise NotImplementedError
    def notify(self, event, detail=None):
        pass

class AIAdaptivePoker(PokerPlayer):
    def __init__(self, actor, bank, game):
        super(AIAdaptivePoker, self).__init__(actor, bank, game)
        self.round_mem = []
        self.phase_mem = []
        self.mem = None #PokerEpisode(game)
        self.episode = None

    def get_move(self, moves):
        print("{}'s turn...".format(self.name))
        #sleep(1)
        opinion = 0
        cue = self.game.find_best_hand(self.hand)
        cue['read'] = self.read_cards(self.hand + self.game.comm_cards)
        for mem in self.actor.memory:
            opinion += mem.retrieve(cue)
        if opinion != 0:
            #opinion = int(opinion // 100)
            print("I HAVE OPINION '{}' for: {} / {}".format(opinion, 
                                                cue['trick'], cue['read']))
            opinion = round(opinion)
        if opinion <= 0:
            if "+0" in moves[1] or "+1)" in moves[1] or "+2)" in moves[1]:
                opinion = 1
            else: opinion = 0
        #opinion += 1
        if opinion > 4: opinion = 4
        while True:
            try: 
                move = moves[opinion]
                print("ADAPTIVE MOVE: {}".format(move))
                return moves[opinion]
            except IndexError: opinion -= 1

    def normalise_bet(self, bet):
        return bet / (self.game.curr_bet - bet)
    
    def get_norm_total_bets(self):
        table = 0
        banks = 0
        for player in self.game.players:
            table += player.bet
            banks += player.bank
        return table / banks

    def notify(self, event, detail=None):
        if event == "move":
            self.episode.moves.append(detail)
        elif event == "end phase":
            ep = {'comm_cards': [], 'moves': self.phase_mem}
            for card in self.game.comm_cards:
                ep['comm_cards'].append(card.compress())
            self.round_mem.append(ep)
            self.phase_mem = []
        elif event == "end round":
            # detail = {player: chips +/-, hand
            outcome = {}
            for player in detail:
                outcome[player.actor] = {'chips': detail[player] / 
                                         self.game.total_chips}
                if player.hand and (player is self or player.is_showing):
                    outcome[player.actor]['hand'] = [card.compress() for card
                                                     in player.hand]
                    cards = player.hand[:]
                    cards += self.game.comm_cards
                    outcome[player.actor]['trick'] = self.game.find_best_hand(
                        cards)['trick']
                    outcome[player.actor]['read'] = self.read_cards(cards)
            ep = {'outcome': outcome, 'phases': self.round_mem}
            self.mem.rounds.append(ep)
            self.round_mem = []
        elif event == "end game":
            self.mem.winner = detail.actor
            self.mem.consolidate()
            self.actor.create_memory("poker", self.mem)
            self.mem = None
        elif event == "start":
            self.episode = PokerEpisode(game)
        else:
            raise ValueError("Undefined action: {}".format(action))
        



class Poker(object):
    def __init__(self, players, ante):
        self.ante = ante
        self.leader = None
        self.turn = 0
        self.curr_bet = 0
        self.room = PokerRoom()
        self.location = None
        self.table = Table()
        self.room.inv.append(self.table)
        self.hierarchy = ['High card', 'Pair', 'Two pairs', 'Three of a kind', 
                          'Flush', 'Straight', 'Full house', 'Four of a kind',
                          'Straight flush']
        self.phase = 0
        self.deck = self.get_new_deck()
        self.comm_cards = []
        self.burn_cards = []
        self.total_chips = 0
        self.players = []# 1st is dealer, then from left
        #self.players.append(HumanPokerPlayer(players[0], 50, self))
        for actor in players: #[1:]:
            self.players.append(players[actor](actor, 50, self))
        for player in self.players: self.total_chips += player.bank

    # returns a complete deck, shuffled
    def get_new_deck(self):
        deck = []
        for suit in ['Clubs', 'Diamonds', 'Hearts', 'Spades']:
            for face in range(2, 15):
                card = PlayingCard(suit, face)
                card.loc['on top of'] = self.table
                card.desc.append('in deck')
                deck.append(card)

        random.shuffle(deck)
        return deck

    def get_hand(self, player):
        return self.find_best_hand(player.hand)

    # Relies on hands being sorted correctly prior
    def compare_hands(self, comp, best):
        if best is None:
            return 'win'
        if comp['trick'] not in self.hierarchy:
            raise ValueError("trick '{}' is undefined".format(comp['trick']))
        if comp['trick'] != best['trick']:
            if (self.hierarchy.index(comp['trick']) > 
                    self.hierarchy.index(best['trick'])):
                return 'win'
            else:
                return 'lose'
        for c in range(5):
            if comp['hand'][c].face > best['hand'][c].face:
                return 'win'
            if comp['hand'][c].face < best['hand'][c].face:
                return 'lose'
        return 'draw'

    def do_show_down(self):
        print("Doing show down")
        best = None
        if self.leader is None: self.leader = self.players[0]
        player = self.leader
        while True:
            if player.is_out:
                result = 'was out'
                print("{} was out".format(player.name))
            elif player.is_folded:
                result = 'fold'
                print("{} had folded".format(player.name))
            else:
                hand = self.get_hand(player)
                result = self.compare_hands(hand, best)
            if result == 'win':
                best = hand
                winners = [player]
                player.is_showing = True
                print("Player {} has {}".format(player.name, best['trick']))
                for card in best['hand']: print(" * {}".format(card.name))
            elif result == 'draw':
                winners.append(player)
                print("Player {} draws".format(player.name))
            elif result == 'lose':
                print("{} is beaten".format(player.name))
            try: 
                next_player = self.players.index(player) + 1
                player = self.players[next_player]
            except IndexError:
                player = self.players[0]
            if player is self.leader:
                break            
        return winners

        #self.award_winners(winners)

    def end_round(self):
        active = []
        for player in self.players: 
            if not player.is_folded and not player.is_out:
                active.append(player)
        if len(active) == 1:
            winners = active
        else:
            winners = self.do_show_down()
        self.award_winners(winners)
        for player in self.players:
            if not player.is_out and len(player.hand) != 2:
                for card in player.hand: print(str(card))
                raise ValueError("Player {} has illegal len hand: {}".format(
                        player.name, len(player.hand)))
            self.deck += player.hand
            player.hand = []
            if player.bet != 0:
                raise ValueError("player {name} has bet: {bet} "
                    "at end of game!".format(name=player.name, bet=player.bet))
        while self.burn_cards: self.deck.append(self.burn_cards.pop())
        while self.comm_cards: self.deck.append(self.comm_cards.pop())
        self.deck = list(set(self.deck))
            
        # new dealer next time
        self.players.append(self.players.pop(0))
        # Kick bankrupt
        for player in self.players:
            if player.bank == 0: 
                player.is_out = True
                print("{} is out of the game".format(player.name))
        #for p in range(len(self.players)):
        #    player = self.players.pop(0)
        #    if player.bank > 0: self.players.append(player)
        #    else: print("%s is out of the game" %(player.name))
        still_in = [player for player in self.players if not player.is_out]
        if len(still_in) > 1:
            self.phase = 0
            #return self.do_new_phase()
        else:
            self.phase = -1
            print("Game over: Winner is {}".format(still_in[0]))
            self.notify("end game", still_in[0])
            still_in[0].actor.poker_wins += 1



    def award_winners(self, winners):
        print("Awarding winners")
        outcome = {player: 0 for player in self.players} 
        if len(winners) > 1: # for side pots
            winners.sort(key=lambda winner: winner.bet)
        # Take back unmeetable bets:
        for player in self.players:
            if player.bet > winners[-1].bet:
                player.bank += player.bet - winners[-1].bet
                player.bet = winners[-1].bet
        # do all pot(s) for winner(s)
        pots = {}
        for winner in winners: pots[winner.bet] = []
        for pot in pots:
            for winner in winners:
                if winner.bet >= pot: pots[pot].append(winner) 
        while len(pots) > 0:
            print(sorted(pots))
            #pot = pots.pop(sorted(pots)[0])
            #pot = sorted(pots).pop(0)
            #pot = pots.pop(sorted(pots)[0])
            pot = sorted(pots)[0]
            for winner in pots[pot]:
                for player in self.players:
                    if player not in winners:
                        if player.bet // len(winners) < pot // len(winners):
                            winnings = player.bet // len(winners)
                        else:
                            winnings = pot // len(winners)
                        print("{winner} wins {x} chips from {name}".format(
                            winner=winner.name, x=winnings, name=player.name))
                        winner.bank += winnings
                        player.bet -= winnings
                        outcome[winner] += winnings
                        outcome[player] -= winnings
            pots.pop(pot)
            new_pots = {}
            for old in pots: new_pots[old-pot] = pots[old]
            pots = new_pots
        # winners take back thier own bets
        for winner in winners:
            winner.bank += winner.bet
            winner.bet = 0
        # remainder, shared to winners from dealer left
        remains = 0
        for player in self.players: 
            remains += player.bet
            outcome[player] -= player.bet
            player.bet = 0
        if remains > 0: print("Remainder chips: {}".format(remains))
        while remains > 0:
            for player in self.players:
                if player in winners:
                    player.bank += 1
                    outcome[player] += 1
                    remains -= 1
                if remains == 0: break
        self.notify("end round", outcome)
                        
            
    def notify(self, event, detail=None):
        #print("NOTIFY: {}, {}".format(event, detail))
        for player in self.players:
            player.notify(event, detail)


    def do_round(self, position=0):
        print(" *" * 5 + "\n New round")
        players = self.players
        self.leader = None
        position = position
        player = players[position]
        while player != self.leader:
            if player.is_out:
                self.notify("move", {player: "out"})
            elif player.is_folded:
                self.notify("move", {player: "folded"})
                print("{} is folded".format(player.name))
            elif player.is_all_in:
                self.notify("move", {player: "all in"})
                print("{} is all in".format(player.name))
            else:
                self.print_status(player)
                move = player.get_move(self.get_available_moves(player))
                move = move.lower()
                if 'fold' in move:
                    player.is_folded = True
                    self.notify("move", {player: "folds"})
                    remaining = []
                    for plyr in self.players: 
                        if not plyr.is_folded and not plyr.is_out:
                            remaining.append(plyr)
                    if len(remaining) == 1:
                        return self.end_round() #self.award_winners(remaining)
                elif '+' in move:
                    bet = int(move[move.index('+')+1:move.index(')')])
                    self.notify("move", {player: move})
                    self.make_bet(player, bet)
            if (self.leader is None and 
                not player.is_folded and not player.is_out):
                self.leader = player
            position += 1
            try: 
                player = players[position]
            except IndexError:
                position = 0
                player = players[position]
        self.notify("end phase", self.phase)

    def get_available_moves(self, player):
        moves = ['Fold']
        diff = self.curr_bet - player.bet
        if diff == 0: call = ""
        else: call = "<call {}> ".format(self.leader)
        if player.bank - diff > 0:
            moves.append('{}Stick (+{})'.format(call, diff))
            if player.bank - diff - self.ante > 0:
                moves.append('{}Raise low (+{})'.format(call, 
                                                        diff + self.ante))
            if player.bank - diff - 2 * self.ante > 0:
                moves.append('{}Raise mid (+{})'.format(call, 
                                                      diff + 2 * self.ante))
            if player.bank - diff - 4 * self.ante > 0:
                moves.append('{}Raise high (+{})'.format(call, 
                                                       diff + 4 * self.ante))
            else:
                moves.append('Raise all in (+{})'.format(player.bank))
        else:
            moves.append('{}Stick (all in +{})'.format(call, player.bank))

        return moves

    def make_bet(self, player, bet):
        if bet < 0:
            raise ValueError("Player {} attempted negative bet {}".format(
                player.name, bet))
        if player.bank < bet:
            if self.phase == 1 and bet > 0:
                bet = player.bank
                print("{} couldn't make full ante".format(player.name))
            else:
                raise ValueError("Player {} attempted illegal bet{} / "
                                 "{}".format(player.name, bet, player.bank))
        player.bet += bet
        player.bank -= bet
        chip_raise = player.bet - self.curr_bet
        if player.bet < self.curr_bet and player.bank != 0:
            raise ValueError("{} attempted illegal call".format(player.name))
        if bet == 0:
            print("{} sticks".format(player.name))
        elif player.bet > self.curr_bet:
            self.curr_bet = player.bet
            self.leader = player
            print("{} raises by {} for total of {}".format(player.name,
                                                chip_raise, player.bet))
        elif player.bet <= self.curr_bet:
            if self.leader == None:
                leader = "ante"
            else:
                leader = self.leader.name
            print("{} calls {} (+{})".format(player.name, leader, bet))
        if player.bank == 0:
            player.is_all_in = True
            print("{} is all in".format(player.name))


    def find_best_hand(self, hand):
        cards = hand[:] # hack..
        cards += self.comm_cards
        cards = list(set(cards))
        #if len(cards) < 5:
        #    return {'trick': Unknown, 'hand': cards} #None
            #raise ValueError("Minimum five cards required")
        #cards.sort(key=lambda card: card.face, reverse=True)
        straight = [cards[0]] # init to first card
        flush = []
        str_flush = []
        flushes = {'Clubs': [], 'Diamonds': [], 'Hearts': [], 'Spades': []}
        matches = {face: [] for face in range(2, 15)}
        hand = []
        trick = None
        for card in cards:
            if type(card.face) is Unknown or type(card.suit) is Unknown:
                return None
            matches[card.face].append(card)
            flushes[card.suit].append(card)
        # Check for (straight) flushes
        for suit in flushes.keys():
            if len(flushes[suit]) < 5:
                continue
            flushes[suit].sort(key=lambda card: card.face, reverse=True)
            run = flushes[suit]
            if flush == [] or flush[0].face < run[0].face:
                flush = run[:5]
            for c in range(len(run) - 4):
                if str_flush != [] and str_flush[0].face >= run[c].face:
                    break
                if run[c].face == run[c+4].face + 5:
                    str_flush = run[c:c+5]
                    break
            if str_flush == [] and run[0].face == ACE and run[-4].face == 5:
                str_flush = run[-4:]
                str_flush.append(run[0])
        if str_flush != []:
            return {'trick': "Straight flush", 'hand': str_flush}
        # Check for rest
        quad = []
        triple = []
        pairs = []
        kickers = []
        straight = []
        for face in range(ACE, 1, -1):
            if len(matches[face]) == 0:
                if len(straight) < 5:
                    straight = []
                continue
            kickers.append(matches[face][0])
            if len(straight) < 5:
                straight.append(matches[face][0])
            if len(matches[face]) == 4 and quad == []:
                quad = matches[face]
                if len(kickers) > 1: break
            elif len(matches[face]) == 3 and triple == []:
                triple = matches[face]
                if pairs != []: break
            elif len(matches[face]) >= 2:
                pairs.append(matches[face][:2])
                if triple != []: break

        if len(straight) == 4 and straight[-1].face == 2:
            try: straight.append(matches[ACE][0])
            except IndexError: pass

        if quad != []:
            trick = "Four of a kind"
            hand = quad
        elif triple != [] and pairs != []:
            trick = "Full house"
            hand = triple
            hand += pairs[0]
        elif flush != []:
            trick = "Flush"
            hand = flush
        elif len(straight) == 5:
            trick = "Straight"
            hand = straight
        elif triple != []:
            trick = "Three of a kind"
            hand = triple
        elif len(pairs) >= 2:
            trick = "Two pairs"
            hand = pairs[0]
            hand += pairs[1]
        elif len(pairs) == 1:
            trick = "Pair"
            hand = pairs[0]
        else:
            trick = "High card"

        high = ACE
        while len(hand) < 5 and len(hand) < len(cards):
            try: 
                card = matches[high][0]
                if card not in hand:
                    hand.append(card)
            except IndexError: pass
            high -= 1

        return {'trick': trick, 'hand': hand}



        
    def print_status(self, player):
        print("\nPlayer: %s, bank: %d chips" %(player.name, player.bank))
        if len(player.hand) < 5:
            print("Hand: ")
            for card in player.hand: print("\t%s" %(card.name))
        else:
            trick = self.find_best_hand(player.hand)
            print("Trick: %s" %(trick.keys()[0]))
            for card in trick.values()[0]: print(card.name)
        if self.leader != None:
            print("Round bet: %d from leader: %s"
                    %(self.curr_bet, self.leader.name))
        print("Player bet: %d" %(player.bet))
                 
          
    def do_new_phase(self):
        raise NotImplementedError

    def run(self):
        self.notify("start")
        self.phase = 1
        while self.phase != -1:
            self.do_new_phase()


class TexasHoldem(Poker):
    #def __init__(self, players, ante):
    #    super(TexasHoldem, self).__init__(players, ante)

    def do_new_phase(self):
        chip_total = 0
        for player in self.players:
            chip_total += player.bet
        print("Chips on table: %d" %(chip_total))
        print("Deck size: {} (set: {})".format(
                    len(self.deck), len(set(self.deck))))

        if self.phase == 1:
            #self.comm_cards = []
            for player in self.players: print(" * {}".format(player.name))
            if len(self.deck) != 52:
                raise ValueError("Deck is wrong size! {} (set: {})".format(
                    len(self.deck), len(set(self.deck))))
            if len(set(self.deck)) != 52:
                raise ValueError("Deck is wrong size! {} (set: {})".format(
                    len(self.deck), len(set(self.deck))))
            random.shuffle(self.deck)
            print("\nShuffling deck for new round\n")
            chip_total = 0
            for player in self.players: chip_total += player.bank
            if chip_total != self.total_chips:
                raise ValueError("Chip total mismatch! {} / {}".format(
                    chip_total, self.total_chips))
            self.curr_bet = 0
            active = []
            for player in self.players:
                player.is_folded = False
                player.is_all_in = False
                player.is_showing = False
                if player.bet != 0: 
                    raise ValueError("{} has rogue leftover bet: {}".format(
                        player.name, player.bet))
                if not player.is_out: active.append(player)
            # Deal hands
            for deal in range(2):
                for player in active:
                    player.hand.append(self.deck.pop(0))
            # Blinds
            print("Posting blinds")
            if len(active) == 2: # dealer is small blind
                #self.players.append(self.players.pop(0))
                self.make_bet(active[1], self.ante // 2)
                self.make_bet(active[0], self.ante)
                self.do_round(1)
            else:
                self.make_bet(active[0], self.ante // 2)
                self.make_bet(active[1], self.ante)
                self.do_round(2)
        elif self.phase == 2:
            print("Flop:")
            self.burn_cards.append(self.deck.pop(0))
            for deal in range(3):
                card = self.deck.pop(0)
                print("\t%s" %(card.name))
                self.comm_cards.append(card)
            self.do_round()
        elif self.phase == 3 or self.phase == 4:
            if self.phase == 3: print("Turn:")
            elif self.phase == 4: print("River:")
            self.burn_cards.append(self.deck.pop(0))
            card = self.deck.pop(0)
            print("\t%s" %(card.name))
            self.comm_cards.append(card)
            self.do_round()
        elif self.phase == 5:
            self.end_round()

        if self.phase == -1: return

        self.phase += 1
        #return self.do_new_phase()


    def print_status(self, player):
        print("Player: %s, bank: %d chips" %(player.name, player.bank))
        print("Hand: ")
        for card in player.hand: print("\t%s" %(card.name))
        if len(self.comm_cards) > 0:
            print("Community: ")
            for card in self.comm_cards: print("\t%s" %(card.name))
            cards = []
            cards += player.hand
            cards += self.comm_cards
            trick = self.find_best_hand(cards)
            print("Trick: %s" %(trick['trick']))
            for card in trick['hand']: print("\t%s" %(card.name))
        if self.leader != None:
            print("Round bet: %d from leader: %s" %(self.curr_bet, 
                self.leader.name))
        print("%s current stake: %d" %(player.name, player.bet))
        

    def get_hand(self, player):
        hand = []
        hand += player.hand
        hand += self.comm_cards
        return self.find_best_hand(hand)

class Player(object):
    def __init__(self, name, bank):
        self.name = name
        self.hand = []
        self.bank = bank
        self.bet = 0
        self.is_folded = False

    def get_decision(self):
        pass

#class PokerError(Exception):
#    pass

# # # # # # # # # # #

humans = {Actor("Daedalus"): AIAdaptivePoker, Actor("Shodan"): AIReactivePoker,
          Actor("Maeve"): AIRandomPoker, Actor("Bethany"): AIConstantPoker}

runs = 0
while runs < 2:
    runs += 1
    game = TexasHoldem(humans, 2)
    game.run()
    print("\n\n\n...* {} *...\n\n\n".format(runs))
    #break


for player in humans:
    print("{} Wins for {} ({})".format(player.poker_wins, player.poker_type, player.name))
