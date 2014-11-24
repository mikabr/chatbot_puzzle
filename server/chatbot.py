import random
import string
import re
import os
import nltk
from nltk.probability import *
from ngram import NgramModel
#from kneserney import KneserNeyProbDist


class ChatBot:

    def __init__(self, characters, models, ngram, debug=False):
        self.characters = characters
        self.models = models
        self.n = ngram
        self.debug = debug

    @staticmethod
    def join_punctuation(seq, punct='.,;?!'):
        charpunctacters = set(punct)
        seq = iter(seq)
        current = next(seq)

        for nxt in seq:
            if nxt in punct:
                current += nxt
            else:
                yield current
                current = nxt

    def generate_response(self, character, seed):
        model = self.models[character]
        len_seed = len(seed)
        response = seed[:]
        while response and not response[-1][-1] in {'.', '!', '?', '?!'}:
            word = model._generate_one(response)
            response.append(word)
        response = response[len_seed:]
        response = self.process_response(response)
#        if not response:
#            response = self.generate_response(character, seed)
#        if len(response.split()) < 3:
#            response = self.generate_response(character, seed)
        return response

    # given a list of words, sanitizes it to return something sentence-like
    @staticmethod
    def process_response(response):

        # removes potentially unmatched punctuation
        bad_punct = {'(', ')', '[', ']', '{', '}', '\"', '`', '<', '>', '~', '``'}
        response = filter(lambda word: all([char not in bad_punct for char in word]), response)
#        response = [word for word in response if word not in {'(', ')', '[', ']', '{', '}', '\"', '`', '<', '>', '~'}]

        if response:
            # removes any leading punctuation
            first = 0
            for i in range(len(response)):
                if all([c not in string.punctuation for c in response[i]]):
                    first = i
                    break
            response = response[first:]
#            if response[0] in string.punctuation:
#                response = response[1:]

        if response:
            # capitalizes the first letter of the first word
            response[0] = response[0].capitalize()

        # puts the words into a string, with spaces between words but not before punctuation
        response = ' '.join(response)
        response = re.sub(r' (?=\W)', '', response)
        return response

    # given a character and an input string, scores how similar the string is to that character's corpus
    # return cross-entropy between character's corpus and input string
    def score_character(self, character, words):
        model = self.models[character]
        if len(words) < self.n:
            for i in range(self.n - len(words)):
                model = model._backoff
        if self.debug:
            print model
        return model.entropy(words)

    # given an input string, scores it's similarity to each character and selects min scoring character
    def classify_input(self, words):
        scores = {}
        if words:
            scores = {character: self.score_character(character, words) for character in self.characters}
            scores = {character: score for character, score in scores.iteritems() if score}
        if self.debug:
            print scores
        if scores:
            best = min(scores, key=lambda c: scores[c])
            return best

    # given a character, returns the next character in the characters list (wrapping last to first)
    def pick_responder(self, input_character):
        return self.characters[(self.characters.index(input_character) + 1) % len(self.characters)]

    def response(self, inp):
        print inp
        tokens = nltk.word_tokenize(inp)
        words = filter(lambda word: all([char not in string.punctuation.replace('-', '') for char in word]), tokens)
        if self.debug:
            print words

        try:
            # classify input as character it's most similar to
            input_character = self.classify_input(words)
            if self.debug:
                print input_character
            if input_character:
                # deterministically pick character to respond as
                responder = self.pick_responder(input_character)
                # generate response from selected character, seeded with user's input
                return self.generate_response(responder, words)
            else:
                return "That's not very interesting..."
        except IOError:
            return "Your input caused a bug. This is NOT part of the puzzle. Please report this bug in testsolving feedback so we can fix it."

    # runs chatbot input/response interface
    def run(self):

        print 'Talk with your new friends. Quit with Q or q.'

        while True:

            # get input from user
            inp = raw_input('\n> ')
            if inp.lower() == 'q':
                break

            words = nltk.word_tokenize(inp)
            words = filter(lambda word: all([char not in string.punctuation.replace('-','') for char in word]), words)
            if self.debug:
                print words

            try:

                # classify input as character it's most similar to
                input_character = self.classify_input(words)
                if self.debug:
                    print input_character
                    
                if input_character:
    
                    # deterministically pick character to respond as
                    responder = self.pick_responder(input_character)
        
                    # generate response from selected character, seeded with user's input
                    response = self.generate_response(responder, words)
                    print response
                    
                else:    
                    print "That's not very interesting..."
                    
            except IOError:
                print "Your input caused a bug. This is NOT part of the puzzle. Please report this bug in testsolving feedback so we can fix it."

def load_corpora(characters):

    char_corps = {}
    for char in characters:
        directory = os.path.join(os.path.dirname(__file__), 'TrainingSets/')
        assert(char in os.listdir(directory))
        corpus = []
        for datafile in os.listdir(directory + char):
            data = open(directory + char + '/' + datafile, 'r').read()
            data = nltk.word_tokenize(data.decode('utf-8', errors='ignore'))
            corpus += data
        char_corps[char] = corpus
    return char_corps
#    return models

def initialize_bot(chars):
    n = 3
    char_corps = load_corpora(chars)
    est = lambda fdist, bins: MLEProbDist(fdist)
#    est = lambda fdist, bins: LidstoneProbDist(fdist, 0.2)
#    est = lambda fdist, bins: WittenBellProbDist(fdist)
#    est = lambda fdist, bins: KneserNeyProbDist(fdist)
    models = {character: NgramModel(n, corp, estimator=est)
              for character, corp in char_corps.iteritems()}
    return ChatBot(chars, models, ngram=n, debug=False)


class memorize(dict):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result

@memorize
def bot1():
    print 'Initializing bot1'
    chars = ['Nash', 'Orwell', 'Nixon', 'Aguilera', 'Rand', 'Yankovic']
    return initialize_bot(chars)
    print 'Initialized bot 1'

@memorize
def bot2():
    print 'Initializing bot2'
    chars = ['Grande', 'Asimov', 'Marx', 'Einstein']
    return initialize_bot(chars)
    print 'Initialized bot 2'

if __name__ == "__main__":
    print 'Please wait...'
    bot1().run()
