#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread
import time 

songs_list = [] # map from id to the filename for the song
QUEUE_LENGTH = 10
RECV_CMD_BUFFER = 64
SEND_BUFFER = 2
close_threads = False
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

def create_list_msg(songs_list):
    content_body = ""
    for i in range(len(songs_list)):
        song_tuple = (i+1, songs_list[i]['name'])
        content_body = content_body + str(song_tuple)
        if (i < len(songs_list)-1):
            content_body = content_body + ","

    return content_body



def send_response(client, client_socket, status, content_body):

    # header
    header_message_length = '10sI4s'
    message_length = header_message_length + str(SEND_BUFFER) + "s"
    # data_to_send = struct.pack(header_message_length,)
    # client_socket.send(data_to_send)

    # send body
    if (len(content_body) <= SEND_BUFFER):
        data_to_send = struct.pack(message_length, client.protocol, status, client.method, content_body)
        client_socket.send(data_to_send)
    else:
        # partial send
        while True:
            partial_content = content_body[:SEND_BUFFER]
            content_body = content_body[SEND_BUFFER:]
            remaining_bytes = len(content_body)
            message_length = header_message_length + str(SEND_BUFFER) + "s"
            data_to_send = struct.pack(message_length, client.protocol, status, client.method, partial_content)
            client_socket.send(data_to_send) 

            if (remaining_bytes == 0):
                break
            elif (remaining_bytes < SEND_BUFFER):
                partial_content = content_body
                message_length = header_message_length + str(SEND_BUFFER) + "s"
                data_to_send = struct.pack(message_length, client.protocol, status, client.method, partial_content)
                client_socket.send(data_to_send)  
                break               


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
            if (client.method in accepted_methods):
                content_body = ""
                if (client.method == 'LIST'):
                    print ("it is LIST")
                    content_body = create_list_msg(songs_list)
                elif (client.method == 'PLAY'):
                    print ("it is PLAY --> song_id: " + str(client.song_id))
                    found_song_filename =  songs_list[client.song_id-1]
                    content_body = open(found_song_filename, 'r').read()
                elif (client.method == 'STOP'):
                    print ("it is STOP")

                elif (client.method == 'EXIT'):
                    print ("it is EXIT")
                    close_threads = True
                    break
                # else:
                #     print ("client_write listening...")
                
                send_response(client, client_socket, 200, content_body)
                


        except (KeyboardInterrupt, SystemExit):
            print "client_write --> keyboardInterrupt"
            close_threads = True
            #break
        except IOError as e:
            print "client_write --> IOError"
            print_except_msg()
            close_threads = True
            #break
        except Exception as e:
            print "client_write --> any exception"
            print_except_msg()
            close_threads = True
            # close_threads = True
            # create 500 response
            # break
            # message = 'Server Error'
            # message_format = '10sI' + str(len(message)) + 's'
            # data_to_send = struct.pack(message_format, client.protocol, 500, message)
            # client_socket.send(data_to_send) 

            # close_threads = True
            # break

        client.method = ''
        client.lock.release()


    



# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client, client_socket, client_port):
    global close_threads
    while not close_threads:
        
        try:

            print "client_read " + str(client_port) + " listening..."
            message_received = client_socket.recv(RECV_CMD_BUFFER)
        
            message_decoded = struct.unpack('4sI10s', message_received)
            print (message_decoded)
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
        except IOError as e:
            print "client_read --> IOError"
            print_except_msg()
            close_threads = True
            break
        except Exception as e:
            print "client_read --> any exception"
            print_except_msg()
            close_threads = True
            break
            # message = 'Server Error'
            # message_format = '10sI' + str(len(message)) + 's'
            # data_to_send = struct.pack(message_format, client.protocol, 500, message)
            # client_socket.send(data_to_send) 


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
            close_threads = True
            break
        except IOError as e:
            print "main --> IOError"
            print_except_msg()
            close_threads = True
            break
        except Exception as e:
            print "main --> any exception"
            print_except_msg()  
            close_threads = True
            # close_threads = True      
            break




    s.close()



if __name__ == "__main__":
    main()
