import socket

SERVER = "127.0.0.1"
PORT = 50051

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER, PORT))

response = 'Y'
data_to_send = "0"

while response == 'Y':
    sock.sendall(bytes(data_to_send, 'UTF-8'))
    data = sock.recv(1024)
    print('Received', repr(data))
    response = input("Send again (Y/N)? ")
    if response == 'Y':
        data_to_send = input("Enter data: ")

sock.close()
