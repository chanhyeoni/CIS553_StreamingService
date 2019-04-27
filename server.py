#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread
import time 

songs_list = [] # map from id to the filename for the song
QUEUE_LENGTH = 10
SEND_BUFFER = 4096
close_threads = False

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
def client_write(client, client_socket, client_port, songs_list):
    global close_threads
    while not close_threads:
        client.lock.acquire()
        try:
            message_body = " "
            if (client.method == 'LIST'):
                print ("it is LIST")
                for i in range(len(songs_list)):
                    song_tuple = (i+1, songs_list[i]['name'])
                    message_body = message_body + str(song_tuple)
                    if (i < len(songs_list)-1):
                        message_body = message_body + ", "

                print message_body
                # for i in range(len(songs)):
                #     song_tuple = (i+1, songs[i]['name'])
            elif (client.method == 'PLAY'):
                print ("it is PLAY --> song_id: " + str(client.song_id))
                # while (True):
                #     data_read = open("filename", "r").read(SEND_BUFFER)
                    # use conn of client to send the data_read (e.g. conn.send(data_read))
            elif (client.method == 'STOP'):
                print ("it is STOP")
            elif (client.method == 'EXIT'):
                print ("it is EXIT")
                close_threads = True
                break
            # else:
            #     print ("client_write listening...")
            client.method = ''
            
        except (KeyboardInterrupt, SystemExit):
            print "client_write --> keyboardInterrupt"
            close_threads = True
            break
        except Exception as e:
            print "client_write --> any exception"
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)

            close_threads = True
            break
        client.lock.release()


    



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client, client_socket, client_port):
    global close_threads
    while not close_threads:
        
        try:

            print "client_read " + str(client_port) + " listening..."
            message_received = client_socket.recv(SEND_BUFFER)
        
            message_decoded = struct.unpack('4sI10s', message_received)
            # print (message_decoded)
            client.lock.acquire()
            client.method = message_decoded[0]
            client.song_id = message_decoded[1]
            client.protocol = message_decoded[2]
            client.lock.release()
            # if (message_decoded[0] == 'EXIT'):
            #     print "client_read --> It's EXIT"
            #     sys.exit(1)
            #     break;
        except (KeyboardInterrupt, SystemExit):
            print "client_read --> keyboardInterrupt"
            close_threads = True
            break
        except Exception as e:
            print "client_read --> any exception"
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            close_threads = True
            break
        



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
    songs_list = get_mp3s(sys.argv[2])
    print songs_list
    threads = []

    # TODO: create a socket and accept incoming connections
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', port))
    s.listen(QUEUE_LENGTH)


    # how can the server 
    # conn = None
    while True:
        try:
            conn, addr = s.accept()
            client = Client()
            # t = Thread(target=on_new_client,args=(conn,addr,client))
            # t.start()
            # message_received = conn.recv(SEND_BUFFER)

            t1 = Thread(target=client_read, args=(client, conn, addr[1]))
            t1.start()
            threads.append(t1)
            # t1.join()
            time.sleep(1)
            t2 = Thread(target=client_write, args=(client, conn, addr[1], songs_list))
            t2.start()
            threads.append(t2)
            # t2.join()

            # for t in threads:
            #     t.join()
        except (KeyboardInterrupt, SystemExit):
            print "main --> keyboardInterrupt"
            break
            
        except Exception as e:
            print "main --> any exception"
            # if hasattr(e, 'message'):
            #     print(e.message)
            # else:
            #     print(e)            
            break




    s.close()



if __name__ == "__main__":
    main()
