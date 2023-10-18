from socket import socket, AF_INET, SOCK_STREAM
HOST = '127.0.0.1'
PORT = 5001

# Test Seller Msg:
# 1 100 10 apple


def client(address, port):
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((address, port))
        content = sock.recv(16)

        if content == b'you are a seller':
            seller_handler(sock)
        elif content == b'you are a buyer':
            buyer_handler(sock)
        elif content == b'Connection rejected!':
            print('Connection rejected!')

                # while response_msg == 'Invalid Auction Request!':
                # client_msg = input("input the message to server:")
                # client_msg = '1 100 10 apple'

    except Exception as e:
        print('client:', e)


def seller_handler(sock):
    # client_msg = input("  input the message to server:")
    client_msg = '2 100 3 apple'
    # client_msg = 'asdf;askdjfalskdfja;slkdgj24eitqj;wrekgnfwa;lsdkfj'

    sock.send(client_msg.encode())

    response_msg = sock.recv(1024)

    if response_msg == b'Invalid Auction Request!':
        print(response_msg.decode())
    elif response_msg == b'seller connection established, waiting for incoming buyers':
        print(response_msg.decode())
        while True:
            response_msg = sock.recv(1024)
            # print(response_msg)
            if response_msg == b'bid round ends!':
                print('seller socket closed!')
                sock.close()
                break
            else:
                print(response_msg.decode())
            # if response_msg == 'All buyers connected!':
            #     break


def buyer_handler(sock):

    client_msg = 'buyer is online'
    sock.send(client_msg.encode())

    while True:
        response_msg = sock.recv(1024)
        # print(response_msg.decode())

        if response_msg == b'Bidding starts!':
            keyboard_input = input('input your bid:')
            sock.send(keyboard_input.encode())
            # print('keyboard input:', keyboard_input)
            # send bid to server
            # response_msg = sock.recv(1024)
            # print(response_msg)
        elif response_msg == b'Bid received!':
            print('Your bid is received!')
            # sock.recv(1024)
        elif response_msg == b'Invalid bid!':
            keyboard_input = input('Invalid bid, please try again:')
            sock.send(keyboard_input.encode())
        elif response_msg == b'bid round ends!':
            print('bid round end!')
            sock.close()
            break
        else:
            print(response_msg.decode())


client(HOST, PORT)