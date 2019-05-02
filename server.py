#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread
import time 

songs_dic = {} # map from id to the filename for the song
QUEUE_LENGTH = 10
RECV_CMD_BUFFER = 4096
SEND_BUFFER = 4096
accepted_methods = ['LIST', 'PLAY', 'STOP', 'EXIT']

# per-client struct
class Client:
    def __init__(self):
        self.lock = Lock()
        #self.server_socket = server_socket
        # self.addr = addr
        self.method = ''
        self.song_id = -1
        self.protocol = 'MyProtocol'


def print_except_msg():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)    

def create_list_msg(songs_dic):
    content_body = ""
    for i, data in songs_dic.items():
        song_tuple = (i, songs_dic[i]['name'])
        content_body = content_body + str(song_tuple)
        if (i < len(songs_dic)-1):
            content_body = content_body + ","

    return content_body



def send_response(client, client_socket, status, content_body):

    # header
    header_message_length = '10sI4sI'
    message_length = header_message_length + str(SEND_BUFFER) + "s"

    # print "message size=" + str(struct.calcsize(message_length))

    # send body
    if (len(content_body) <= SEND_BUFFER):
        data_to_send = struct.pack(message_length, client.protocol, status, client.method, client.song_id, content_body)
        client_socket.send(data_to_send)
    else:
        # partial send
        body_size = len(content_body)
        remaining_bytes = body_size

        while (remaining_bytes > 0):
            if (remaining_bytes < SEND_BUFFER):
                print "this is the last chunk"
                partial_content = content_body
            else:
                partial_content = content_body[:SEND_BUFFER]
            
            message_length = header_message_length + str(SEND_BUFFER) + "s"
            data_to_send = struct.pack(message_length, client.protocol, status, client.method, client.song_id, partial_content)
            client_socket.send(data_to_send)

            content_body = content_body[SEND_BUFFER:]
            remaining_bytes = len(content_body)            

        # while True:
        #     partial_content = content_body[:SEND_BUFFER]
        #     content_body = content_body[SEND_BUFFER:]
        #     remaining_bytes = len(content_body)
        #     message_length = header_message_length + str(SEND_BUFFER) + "s"
        #     data_to_send = struct.pack(message_length, client.protocol, status, client.method, client.song_id, partial_content)
        #     client_socket.send(data_to_send) 
        #     # print ("data sent!")
        #     # in PLAY, I have checked, data_to_send is different, which means we did send something

        #     if (remaining_bytes == 0):
        #         break
        #     elif (remaining_bytes < SEND_BUFFER):
        #         print "this is the last chunk"
        #         partial_content = content_body
        #         message_length = header_message_length + str(SEND_BUFFER) + "s"
        #         data_to_send = struct.pack(message_length, client.protocol, status, client.method, client.song_id, partial_content)
        #         client_socket.send(data_to_send)  
        #         break               


# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client, client_socket, client_port, songs_dic, musicdir):
    while True:
        client.lock.acquire()
        try:
            
            if (client.method in accepted_methods):
                content_body = ""
                if (client.method == 'LIST'):
                    print ("from " + str(client_port)+ ":  it is LIST")
                    content_body = create_list_msg(songs_dic)
                    
                elif (client.method == 'PLAY'):
                    print ("from " + str(client_port)+ ":  it is PLAY --> song_id: " + str(client.song_id))
                    found_song_filename =  songs_dic[client.song_id]['name']
                    content_body = open(musicdir + "/" + found_song_filename, 'r').read()
                    
                elif (client.method == 'STOP'):
                    print ("from " + str(client_port)+ ":  it is STOP")
                    content_body = 'Stop requested'
                elif (client.method == 'EXIT'):
                    print ("from " + str(client_port)+ ":  it is EXIT")
                    break
                
                send_response(client, client_socket, 200, content_body)
             
        except (KeyboardInterrupt, SystemExit):
            print "client_write --> keyboardInterrupt"
            break
        except KeyError as e:
            print "client_write --> KeyError (file requrested was not found)"
            print str(e)
            print_except_msg()
            send_response(client, client_socket, 404, '404: File not found')
        except Exception as e:
            print "client_write --> any exception"
            print str(e)
            print_except_msg()
            send_response(client, client_socket, 500, '500: Server Error')

        client.method = ''
        client.lock.release()
        
        
    print "client_write " + str(client_port) + " closed "

    return 0

    



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client, client_socket, client_port):

    print "client_read " + str(client_port) + " listening..."
    while True: 
        try:
            message_received = client_socket.recv(RECV_CMD_BUFFER)

            if (len(message_received) > 0):
                message_decoded = struct.unpack('4sI10s', message_received)
                client.lock.acquire()
                client.method = message_decoded[0]
                client.song_id = message_decoded[1]
                client.protocol = message_decoded[2]
                client.lock.release()
            else:
                print "message received is zero; if it is zero, it means the client is diconnected"
                client.method = 'EXIT'
                break

        except (KeyboardInterrupt, SystemExit):
            print "client_read --> keyboardInterrupt"
            break
        except Exception as e:
            print "client_read --> any exception"
            print_except_msg()
            print str(e)

    print "client_read " + str(client_port) + " closed "

    return 0

def get_mp3s(musicdir):
    print("Reading music files...")
    songs = {}
    counter = 1
    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue
        else:
            filesize = os.path.getsize(musicdir + "/" + filename)
            data = {'name': filename, 'size': filesize}
            songs[counter] = data
            counter = counter + 1
            
        # TODO: Store song metadata for future use.  You may also want to build
        # the song list once and send to any clients that need it.

    print("Found {0} song(s)!".format(len(songs.keys())))

    return songs



def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python server.py [port] [musicdir]")
    if not os.path.isdir(sys.argv[2]):
        sys.exit("Directory '{0}' does not exist".format(sys.argv[2]))

    port = int(sys.argv[1])
    songs_dic = get_mp3s(sys.argv[2])
    print songs_dic
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

            t1 = Thread(target=client_read, args=(client, conn, addr[1]))
            t1.start()
            threads.append(t1)
            time.sleep(1)
            t2 = Thread(target=client_write, args=(client, conn, addr[1], songs_dic, sys.argv[2]))
            t2.start()
            threads.append(t2)
        except (KeyboardInterrupt, SystemExit):
            print "main --> keyboardInterrupt"
            break


    s.close()

    print "server closed"



if __name__ == "__main__":
    main()
