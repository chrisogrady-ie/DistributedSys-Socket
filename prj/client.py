# Christopher O'Grady
# R00067022
# christopher.ogrady@mycit.ie

import socket
import grpc
import pika
import threading
import game_pb2
import game_pb2_grpc


SERVER = "127.0.0.1"
PORT = 50051

def new_message_thread():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='fanout')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='logs', queue=queue_name)

    def callback(ch, method, properties, body):
        print("\n%r \nEnter a guess:" % body)

    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


def run():
    """""
    sock = socket.socket()
    sock.connect((SERVER, PORT))
    """""

    messageThread = threading.Thread(target=new_message_thread,)
    messageThread.start()
    p_name = input("enter name:")
    with grpc.insecure_channel('127.0.0.1:{}'.format(PORT)) as channel:
        stub = game_pb2_grpc.GameRoundStub(channel)
        response = stub.guess_letter(game_pb2.ClientInput(single_guess="", player_name=p_name))
        print(response.message)

        game_on = True
        while game_on:
            user_guess = input("Please wait your turn")
            response = stub.guess_letter(game_pb2.ClientInput(single_guess=user_guess, player_name=p_name))
            print(response.message)
            # uses the server response to know if the word has been guessed
            game_on = response.game_continue
        print("- - - - - -G A M E  O V E R - - - - - -")


run()
