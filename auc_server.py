import select
import threading
from socket import socket, AF_INET, SOCK_STREAM

HOST = '127.0.0.1'
PORT = 5001

# Massage Format:
#
# Seller Mode:
# <type_of_auction> <lowest_price> <number_of_bids> <item_name>
#
# Buyer Mode:
#   1. If the client receives message from the server to wait for other Buyer or start bidding, it
#   holds the role of a Buyer.
#   2. When the bidding starts, the Buyer sends its bid (a positive integer value) to the server.
#   3. If the server indicates an invalid bid, the client must resend a valid bid.
#   4. If the server indicates “Bid received”, the client waits for the final result of the auction.
#


num_of_buyers = -1
type_of_the_auction = -1
item_name = ''
lowest_price = -1
status = 0  # 0: Seller Mode, 1: Buyer Mode
seller_client = None
seller_addr = None
client_connections = []
bidding_start = False


def server(address, port):
    global seller_client, seller_addr, client_connections, bidding_start

    welcome_socket = socket(AF_INET, SOCK_STREAM)
    welcome_socket.bind((address, port))
    welcome_socket.listen(5)

    while True:
        connections_count = len(client_connections)
        if status == 0:
            print("Auctioneer is ready for hosting auctions!")
            seller_client, seller_addr = welcome_socket.accept()
            print('seller address ', seller_client.getpeername())
            # seller_thread = threading.Thread(target=seller_handler, args=(seller_client, ))
            seller_handler(seller_client)
            # print('seller thread created!')
            # seller_thread.start()

        elif status == 1:
            if connections_count < num_of_buyers:
                buyer_client, buyer_addr = welcome_socket.accept()
                print('buyer address ', buyer_client.getpeername())
                client_connections.append(buyer_client)
                response_msg = ('New incoming buyer!' + ' current connections:' + str(len(client_connections))).encode()
                seller_client.send(response_msg)

                buyer_handler(buyer_client, len(client_connections))

                connections_count = len(client_connections)
                print('current connections:', connections_count)

                # for client in client_connections:
                #     client.send('waiting for other buyers to connect...'.encode())

                if connections_count == num_of_buyers:
                    print('All buyers connected!')
                    seller_client.send(b'All buyers connected!')
                    for client in client_connections:
                        client.send(b'All buyers connected!')

                    bidding_thread = threading.Thread(target=bidding_handler)
                    bidding_thread.start()
                    print('status', status)
            else:
                buyer_client, buyer_addr = welcome_socket.accept()
                buyer_client.send(b'Connection rejected!')
                # while bidding_start:
                #     print('loop start!')
                #     incoming_socket, addr = welcome_socket.accept()
                #     if incoming_socket is not None:
                #         incoming_socket.send(b'Connection rejected!')
                #         incoming_socket.close()
                # print('loop break')
            # else:
            #     print('Waiting for other buyers to connect...')
            #     for client in client_connections:
            #         client.send(b'Waiting for other buyers to connect...')


def seller_handler(client):
    global type_of_the_auction, lowest_price, num_of_buyers, item_name, status  # Declare as global
    try:
        client.send(b'you are a seller')
        msg = client.recv(1024)
        msg = msg.decode()
        params = msg.split(' ')
        # print('params:', params[0], params[1], params[2], params[3])

        type_of_the_auction = int(params[0])
        lowest_price = int(params[1])
        num_of_buyers = int(params[2])
        item_name = params[3]

        # print(type_of_the_auction, lowest_price, num_of_buyers, item_name)
        print('Auction request received!:', msg)
        client.send(b'seller connection established, waiting for incoming buyers')
        status = 1

    except Exception as e:
        print('Error:', e)
        client.send(b'Invalid Auction Request!')
        client.close()
        print('Invalid Auction Request!')


def buyer_handler(client, connections_count):
    global client_connections
    client.send(b'you are a buyer')
    print('waiting for buyers, current connections:', connections_count)
    msg = client.recv(1024).decode()
    print('buyer msg received: [', msg, ']')
    readable, writable, exceptional = select.select([], client_connections, [])
    for sock in writable:
        sock.send(b'waiting for other buyers to connect...!')


def bidding_handler():
    global seller_client, seller_addr, client_connections, type_of_the_auction, \
        lowest_price, item_name, bidding_start, status

    bidding_start = True
    try:
        print('Bidding starts!')

        seller_client.send(b'Bidding starts!')
        for client in client_connections:
            client.send(b'Bidding starts!')

        biding_info = {}

        while True:
            if len(biding_info) < num_of_buyers:
                readable, writable, exceptional = select.select(client_connections, [], [])
                for sock in readable:
                    data = sock.recv(1024).decode()
                    print('data from buyer: ', data)
                    biding_info[sock] = int(data)
                    try:
                        data = int(data)
                        print(sock.getpeername(), ' bid ', data)
                        sock.send(b'Bid received!')
                    except Exception as e:
                        print('Error:', e)
                        sock.send(b'Invalid bid!')
            else:
                break

        highest_bid = -1
        second_highest_bid = -1
        second_winner_client = None
        winner_client = None

        for key, value in biding_info.items():
            if value > highest_bid:
                second_highest_bid = highest_bid
                second_winner_client = winner_client
                highest_bid = value
                winner_client = key
        if type_of_the_auction == 1:
            if highest_bid >= lowest_price:
                print('The winner is ', winner_client.getpeername(), ' with bid ', highest_bid)
                winner_client.send(b'You win the bid!')

                for client in client_connections:
                    if client != winner_client:
                        client.send(b'You lose the bid!')

                seller_client.send(b'The winner is ' + str(winner_client.getpeername()).encode()
                                   + b' with bid ' + str(highest_bid).encode() + b'\n')

                # end this round of bidding
                seller_client.send(b'bid round ends!')

                for client in client_connections:
                    client.send(b'bid round ends!')
            else:
                print('No winner!')
        elif type_of_the_auction == 2:
            if second_highest_bid >= lowest_price:
                print('The winner is ', second_winner_client.getpeername(), ' with bid ', second_highest_bid)
                second_winner_client.send(b'You win the bid!')

                for client in client_connections:
                    if client != second_winner_client:
                        client.send(b'You lose the bid!')

                seller_client.send(b'The winner is ' + str(second_winner_client.getpeername()).encode()
                                   + b' with bid ' + str(second_highest_bid).encode())

                seller_client.send(b'bid round ends!')

                for client in client_connections:
                    client.send(b'bid round ends!')
            else:
                print('No winner!')
        bidding_start = False
        status = 0
        print('bidding thread end!')
    except Exception as e:
        print('Error:', e)


server(HOST, PORT)
