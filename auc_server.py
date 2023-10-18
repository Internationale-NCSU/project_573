import select
import sys
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
client_id_mapping = {}
seller_thread = None
bidding_end = False


def reject_new_connection(incoming_socket):
    global seller_client
    while seller_client is not None and bidding_start is False:
        try:
            incoming_socket, addr = incoming_socket.accept()
            if incoming_socket is not None:
                incoming_socket.send(b'Connection rejected!')
        except Exception as e:
            print('Error:', e)


def server(address, port):
    global seller_client, seller_addr, client_connections, bidding_start, seller_thread

    welcome_socket = socket(AF_INET, SOCK_STREAM)
    welcome_socket.bind((address, port))
    welcome_socket.listen(5)

    while True:
        if status == 0 and seller_thread is None:
            print("Auctioneer is ready for hosting auctions!")
            seller_thread = threading.Thread(target=seller_handler, args=(welcome_socket,))
            seller_thread.start()
        elif status == 1:
            buyer_client, buyer_addr = welcome_socket.accept()
            print('buyer address ', buyer_client.getpeername())
            client_connections.append(buyer_client)

            reject_thread = threading.Thread(target=reject_new_buyer_connection, args=(welcome_socket,))
            reject_thread.start()

            # response_msg = ('New incoming buyer!' + ' current connections:' + str(len(client_connections))).encode()
            # seller_client.send(response_msg)

            buyer_handler(buyer_client, len(client_connections))

            connections_count = len(client_connections)
            if connections_count == num_of_buyers:
                print('Requested number of bidders arrived, Let\'s start bidding')
                bidding_thread = threading.Thread(target=bidding_handler)
                bidding_thread.start()
                print('status', status)


def reject_new_buyer_connection(welcome_socket):
    while len(client_connections) >= num_of_buyers and not bidding_end:
        try:
            incoming_socket, addr = welcome_socket.accept()
            if incoming_socket is not None:
                incoming_socket.send(b'Connection rejected!')
        except Exception as e:
            print('Error:', e)



def seller_handler(welcome_socket):
    global type_of_the_auction, lowest_price, num_of_buyers, \
        item_name, status, seller_client, seller_addr, bidding_start  # Declare as global

    seller_client, seller_addr = welcome_socket.accept()
    seller_client.send(b'Your role is [Seller]!')
    #  block all the  incoming connections
    rejection_thread = threading.Thread(target=reject_new_connection, args=(welcome_socket,))
    rejection_thread.start()



    print('Seller is connected from: ', seller_client.getpeername())
    while seller_client is not None and bidding_end is False:
        try:
            msg = seller_client.recv(1024)
            msg = msg.decode()
            params = msg.split(' ')

            # print('params:', params[0], params[1], params[2], params[3])
            try:
                type_of_the_auction = int(params[0])
                lowest_price = int(params[1])
                num_of_buyers = int(params[2])
                item_name = params[3]

            # print(type_of_the_auction, lowest_price, num_of_buyers, item_name)
                print('Auction request received! Now wait for buyers!')
                seller_client.send(b'Auction start')

                bidding_start = True
                status = 1
            except Exception as e:
                seller_client.send(b'Invalid Auction Request!')
                print('Invalid Auction Request!')

        except Exception as e:
            print('Error:', e)
           #  seller_client.close()



def buyer_handler(client, connections_count):
    global client_connections, client_id_mapping
    client.send(b'Your role is [Buyer]!')
    client_id_mapping[client] = connections_count
    print('Buyer', connections_count, 'is connected from: ', client.getpeername())

    # msg = client.recv(1024).decode()
    # print('Buyer', connections_count, ' bid$', msg)
    # readable, writable, exceptional = select.select([], client_connections, [])
    # for sock in writable:
    #     sock.send(b'waiting for other buyers to connect...!')


def broadcast(msg):
    global client_connections, seller_client

    for client in client_connections:
        client.send(msg)
    seller_client.send(msg)


def bidding_handler():
    global seller_client, seller_addr, client_connections, type_of_the_auction, \
        lowest_price, item_name, bidding_start, status, bidding_end, seller_thread

    bidding_start = True
    try:
        print('Bidding starts!')

        broadcast(b'Bidding starts!')
        biding_info = {}
        while True:
            if len(biding_info) < num_of_buyers:
                readable, writable, exceptional = select.select(client_connections, [], [])
                for sock in readable:
                    data = sock.recv(1024).decode()
                    # print('data from buyer: ', data)
                    biding_info[sock] = int(data)
                    try:
                        data = int(data)
                        print('Buyer ', client_id_mapping[sock], ' bid $', data)
                        sock.send(b'Bid received!')
                    except Exception as e:
                        print('Error:', e)
                        sock.send(b'Invalid auction request!')
            else:
                break

        highest_bid = -1
        second_highest_bid = -1
        # second_winner_client = None
        winner_client = None

        for key, value in biding_info.items():
            if value > highest_bid:
                second_highest_bid = highest_bid
                # second_winner_client = winner_client
                highest_bid = value
                winner_client = key

        if highest_bid >= lowest_price:

            if type_of_the_auction == 1:
                print('The winner is ', winner_client.getpeername(), ' with bid ', highest_bid)
                winner_client.send(
                    b'Auction finished!\nYou won this item' + item_name.encode() + b'! Your payment due is' +
                    str(highest_bid).encode() + b'!')
                seller_client.send(
                    b'Auction finished!\nSuccess! Your item' + item_name.encode() + b' is sold for ' +
                    str(highest_bid).encode() + b'!')

            elif type_of_the_auction == 2:
                print('The winner is ', winner_client.getpeername(), ' with bid ', second_highest_bid)
                winner_client.send(
                    b'Auction finished!\nYou won this item' + item_name.encode() + b'! Your payment due is' +
                    str(second_highest_bid).encode() + b'!')
                seller_client.send(
                    b'Auction finished!\nSuccess! Your item' + item_name.encode() + b' is sold for ' +
                    str(second_highest_bid).encode() + b'!')

            for client in client_connections:
                if client != winner_client:
                    client.send(b'Auction finished!\nUnfortunately you did not win in the last round.')



            # end this round of bidding
            broadcast(b'Bid round ends!')

            # close all the connections
            for client in client_connections:
                client.close()
            seller_client.close()

        else:
            print('No winner!')
            # end this round of bidding
            seller_client.send(b'Sorry, this item is not sold!')
            for client in client_connections:
                client.send(b'Auction finished!\nUnfortunately you did not win in the last round.')
            broadcast(b'Bid round ends!')

            for client in client_connections:
                client.close()
            seller_client.close()

        bidding_start = False
        bidding_end = True
        seller_thread = None
        status = 0
        print('bidding thread end!')
    except Exception as e:
        print('Error:', e)


if __name__ == "__main__":
    args = sys.argv
    PORT = int(args[1])
    server(HOST, PORT)