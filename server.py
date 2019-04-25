#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread

songlist_to_send = []
QUEUE_LENGTH = 10
SEND_BUFFER = 4096

# per-client struct
class Client:
    def __init__(self, server_socket):
        self.lock = Lock()
        #self.server_socket = server_socket
        self.server_sock = server_socket 
        # self.conn = conn
        # self.addr = addr
        self.method = ''

        self.song_id = None
        self.song_list = None




# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client):

    if (client.method == 'LIST'):
        
    elif (client.method == 'PLAY'):
        
        while (True):
            # data_read = open("filename", "r").read(SEND_BUFFER)
            # use conn of client to send the data_read (e.g. conn.send(data_read))
    elif (client.method == 'STOP'):



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client):
    conn, addr = client.server_socket.accept()
    message_received = client.conn.recv(SEND_BUFFER)

    print (message_received)

    # check the protocol?

    # parse the message
    arguments_list = message_received.split(" ")

    # add the argument to the data
    client.method = arguments_list[0]

    if (client.method == 'PLAY'):
        client.song_id = arguments_list[1]



    




def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    songlist = []

    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue
        else:
            songlist.append(filename)

        # TODO: Store song metadata for future use.  You may also want to build
        # the song list once and send to any clients that need it.
        
        songs.append(None)

    print("Found {0} song(s)!".format(len(songs)))

    return songs, songlist


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python server.py [port] [musicdir]")
    if not os.path.isdir(sys.argv[2]):
        sys.exit("Directory '{0}' does not exist".format(sys.argv[2]))

    port = int(sys.argv[1])
    songs, songlist = get_mp3s(sys.argv[2])
    threads = []

    # TODO: create a socket and accept incoming connections
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(QUEUE_LENGTH)

    # I feel like Client objects should be created as many as QUEUE_LENGTH


    # how can the server 
    while True:

        client = Client(s)
        t = Thread(target=client_read, args=(client))
        threads.append(t)
        t.start()
        t = Thread(target=client_write, args=(client))
        threads.append(t)
        t.start()




    s.close()


if __name__ == "__main__":
    main()