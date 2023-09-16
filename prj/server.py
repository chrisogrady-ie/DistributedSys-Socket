# Christopher O'Grady
# R00067022
# christopher.ogrady@mycit.ie

# TODO : bugs do exist, user input is not cleaned, must be lowercase
#   and accented letters in read file will make game impossible,
#   game only runs properly once
#   players must be 1 and 2 respectfully when asked for name
#   both players will get fanout response so it may get a little confusing

import pika
from concurrent import futures
import random
import grpc
import game_pb2
import game_pb2_grpc
import socket


LOCALHOST = "127.0.0.1"
PORT = 50051


# decorator to turn letters lowercase and clean '\n'
def clean_string(func):
    def wrapper(*args, **kwargs):
        clean = func(*args, **kwargs)
        return [line.lower().rstrip("\n") for line in clean]
    return wrapper


# reads phrase from file, uses decorator
@clean_string
def phrase_lookup():
    temp_array = []
    with open("phrases.txt") as temp_file:
        for line in temp_file:
            temp_array.append(line)
    return temp_array


# populates a list the same size as phrase read and fills in '_' for letters and spaces
def populate_mystery_list(myst):
    mystery = myst
    counter = 0
    for x in myst:
        if x == "'" or x == "-" or x =="," or x == " ":
            mystery[counter] = myst[counter]
        else:
            mystery[counter] = "_"
        counter += 1
    return mystery


# singleton implementation, only 1 can exist
class LookupCacheSingleton:
    __instance = None

    # returns a random phrase in the populated list
    def random_phrase(self):
        return random.choice(self.phrase_list)

    # creates an instance if there is none
    @staticmethod
    def get_instance():
        if LookupCacheSingleton.__instance is None:
            LookupCacheSingleton(phrase_lookup())
        return LookupCacheSingleton.__instance

    def __init__(self, phrase_list):
        if LookupCacheSingleton.__instance is not None:
            print("new phrase fetched")
        else:
            self.phrase_list = phrase_list
            LookupCacheSingleton.__instance = self


# our game round
class GameRound(game_pb2_grpc.GameRoundServicer):

    def __init__(self):
        self.game_on = True
        self.guess_status = "miss"
        self.answer_list = []
        self.mystery_list = []
        # hard coding 2 player into game, player must enter 1 and 2
        self.players = {"1": 1, "2": 1}

        # answer and mystery list to be generated from singleton
        cache = LookupCacheSingleton.get_instance()
        answer = cache.random_phrase()
        self.answer_list = list(answer)
        self.mystery_list = populate_mystery_list(list(answer))
        # only display on server tab for testing purposes
        print(self.answer_list)

    # check if guess is in phrase
    def is_it_there(self, letter, name):
        score = 0
        counter = 0
        for x in self.answer_list:
            if x == letter and self.mystery_list[counter] != letter:
                self.mystery_list[counter] = letter
                self.guess_status = "hit!"
                score += 1
            counter += 1
        if self.guess_status == "miss!":
            score = -1
        self.players[name] = (self.players[name] + score)
        print("Player: " + name)
        print("Score: ",  self.players[name], "\n")

        # RabbitMQ message handled here
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='logs', exchange_type='fanout')
        message = ("Other player has guessed " + letter + " -> " + ' '.join(self.mystery_list))
        channel.basic_publish(exchange='logs', routing_key='', body=message)
        print("\nSent %r" % message)
        connection.close()

    # if the input is greater than 1 letter, we interpret it as a full guess, if correct game over
    def guess_the_word(self, req):
        word = list(req)
        if word == self.answer_list:
            self.mystery_list = self.answer_list
            self.guess_status = "Correct guess of the phrase!"
            self.game_on = False
        else:
            self.guess_status = "Wrong guess of the phrase!"

    # if word is fully guessed, game is over
    def is_game_continuing(self, name):
        if self.mystery_list == self.answer_list:
            # RabbitMQ message informing of the winner
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
            channel.exchange_declare(exchange='logs', exchange_type='fanout')
            message = ("Player " + name + " wins!")
            channel.basic_publish(exchange='logs', routing_key='', body=message)
            print("\nSent %r" % message)
            connection.close()
            return False
        else:
            return True

    # returns output to client
    def guess_letter(self, request, context):
        self.guess_status = "miss!"
        if len(request.single_guess) > 1:
            self.guess_the_word(request.single_guess)
        else:
            self.is_it_there(request.single_guess, request.player_name)
        self.game_on = self.is_game_continuing(request.player_name)
        return game_pb2.ServerOutput(message='You guessed: \"{0}\" That\'s a {1}\nYou have {2} points\n'
                                     .format(request.single_guess, self.guess_status,
                                             self.players[request.player_name]),
                                     game_continue=self.game_on)


# runs the server
def serve():
    """""
    s = socket.socket()
    s.bind((LOCALHOST, PORT))
    s.listen(2)
    conn, address = s.accept()
    """""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    game_pb2_grpc.add_GameRoundServicer_to_server(GameRound(), server)
    server.add_insecure_port('127.0.0.1:{}'.format(PORT))
    print("Game Server Opened,\n THIS TAB IS FOR ADMIN ONLY")
    server.start()
    server.wait_for_termination()


serve()
