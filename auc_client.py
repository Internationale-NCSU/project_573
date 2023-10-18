import sys
from socket import socket, AF_INET, SOCK_STREAM

HOST = '127.0.0.1'
PORT = 5001


# Test Seller Msg:
# 1 100 10 apple
bid_received = False
bid_end = False


def client(address, port):
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((address, port))
        content = sock.recv(1024)

        if content == b'Your role is [Seller]!':
            print(content.decode())
            seller_handler(sock)
        elif content == b'Your role is [Buyer]!':
            print(content.decode())
            buyer_handler(sock)
        elif content == b'Connection rejected!':
            print('Server is busy, please try again later.')
            sock.close()
    except Exception as e:
        print('Errors happened on client side:', e)
        sock.close()


def seller_handler(sock):
    global bid_end
    while not bid_end:
        client_msg = input("Please submit auction request:")
        sock.send(client_msg.encode())
        response_msg = sock.recv(1024)

        if response_msg == b'Invalid Auction Request!':
            print(response_msg.decode())
            continue
        elif response_msg == b'Auction start':
            print(response_msg.decode())
            while True:
                response_msg = sock.recv(1024)
                # print(response_msg)
                if response_msg == b'Bid round ends!':
                    print('seller socket closed!')
                    bid_end = True
                    sock.close()
                    break
                else:
                    print(response_msg.decode())
                # if response_msg == 'All buyers connected!':
                #     break


def buyer_handler(sock):
    global bid_received
    # client_msg = 'buyer is online'
    response_msg = sock.recv(1024)
    if response_msg == b'Bidding starts!':
        while True:
            if not bid_received:
                keyboard_input = input('Please submit your bid:')
                sock.send(keyboard_input.encode())
            response_msg = sock.recv(1024)  # receive the bid result
            if response_msg == b'Bid received!':
                bid_received = True
                print('Bid received. Please wait...')
                # sock.recv(1024)
            elif response_msg == b'Invalid auction request!':
                print('Invalid bid, please submit a positive integer!')
                continue
            elif response_msg == b'Bid round ends!':
                print('Disconnecting from the Auctioneer server. Auction is over!')
                sock.close()
                break
            else:
                print(response_msg.decode())


# client(HOST, PORT)

if __name__ == "__main__":
    args = sys.argv
    HOST = args[1]
    PORT = int(args[2])
    client(HOST, PORT)
