#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread

songs_dic = {} # map from id to the filename for the song
QUEUE_LENGTH = 10
SEND_BUFFER = 4096

# per-client struct
class Client:
    def __init__(self):
        self.lock = Lock()
        #self.server_socket = server_socket
        # self.addr = addr
        self.method = ''
        self.song_id = -1
        self.protocol = ''




# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client):

    if (client.method == 'LIST'):
        print ("it is LIST")
    elif (client.method == 'PLAY'):
        print ("it is PLAY --> song_id: " + str(client.song_id))
        # while (True):
        #     data_read = open("filename", "r").read(SEND_BUFFER)
            # use conn of client to send the data_read (e.g. conn.send(data_read))
    elif (client.method == 'STOP'):
        print ("it is STOP")



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client, message_received):

    message_decoded = struct.unpack('4sI10s', message_received)
    print (message_decoded)

    # parse the message
    client.method = message_decoded[0]
    client.song_id = message_decoded[1]
    client.protocol = message_decoded[2]


def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue
        else:
            filesize = os.path.getsize(musicdir + "/" + filename)
            data = {'name': filename, 'size': filesize}
            songs.append(data)
            
        # TODO: Store song metadata for future use.  You may also want to build
        # the song list once and send to any clients that need it.

    print("Found {0} song(s)!".format(len(songs)))

    return songs


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



    # how can the server 
    while True:
        print "listening..."
        conn, addr = s.accept()
        print "connected!"
        client = Client()
        message_received = conn.recv(SEND_BUFFER)

        t1 = Thread(target=client_read, args=(client, message_received))
        threads.append(t1)
        t1.start()
        t2 = Thread(target=client_write, args=(client,))
        threads.append(t2)
        t2.start()



    s.close()


if __name__ == "__main__":
    main()