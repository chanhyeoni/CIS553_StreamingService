#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread

code_received = -1
songlist_to_send = []
QUEUE_LENGTH = 10
SEND_BUFFER = 4096

# per-client struct
class Client:
    def __init__(self, server_socket, songlist):
        self.lock = Lock()
        #self.server_socket = server_socket
        conn, addr = server_socket.accept() 
        self.conn = conn
        self.addr = addr
        self.songs_list = songlist


# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client, code_received):
    # if list, code is 0
    # if play, code is 1
    # if stop, code is 2

    if (code_received == 0):
        songlist_to_send = client.songs_list
    elif (code_received == 1):

    elif (code_received == 2):



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client):
    # if list, code is 0
    # if play, code is 1
    # if stop, code is 2
    code_received = client.conn.recv(1)
        




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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(QUEUE_LENGTH)

    # I feel like Client objects should be created as many as QUEUE_LENGTH


    # how can the server 
    while True:

        client = Client(s, songlist)
        t = Thread(target=client_read, args=(client))
        threads.append(t)
        t.start()
        t = Thread(target=client_write, args=(client))
        threads.append(t)
        t.start()




    s.close()


if __name__ == "__main__":
    main()