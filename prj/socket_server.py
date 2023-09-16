# R00067022

import socket
import threading


# handling each connection of a client
# modified from lecture notes to include check against previous high score
# and provide an appropriate response to the client
class ClientThread(threading.Thread):

    def __init__(self, client_address, client_socket, identity):
        threading.Thread.__init__(self)
        self.c_socket = client_socket
        print("Connection no. " + str(identity))
        print("New connection added: ", client_address)

    def run(self):
        print("Connection from : ", clientAddress)
        while True:
            data = self.c_socket.recv(2048)
            if not data:
                break
            msg = int(data.decode())
            if msg > hs.get_score():
                hs.set_score(msg)
                print("NEW HIGH SCORE - > ", msg)
                self.c_socket.send(bytes("New High Score!!! -> " + str(msg), 'UTF-8'))
            else:
                self.c_socket.send(bytes("Record sits at: -> " + str(hs.get_score()), 'UTF-8'))
                print("from client", msg)

        print("Client at ", clientAddress, " disconnected...")


# class to track high score
class HighScore:
    def __init__(self, num):
        self.score = num

    def set_score(self, num):
        self.score = num

    def get_score(self):
        return self.score


# instansiating a record at 0 when the server boots up
hs = HighScore(0)


LOCALHOST = "127.0.0.1"
PORT = 50051

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))

print("Server started")
print("Waiting for client request..")

counter = 0

while True:
    server.listen(1)
    my_socket, clientAddress = server.accept()
    counter = counter + 1
    new_thread = ClientThread(clientAddress, my_socket, counter)
    new_thread.start()
