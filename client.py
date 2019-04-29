#!/usr/bin/env python

import ao
import mad
import readline
import socket
import struct
import sys
import threading
from time import sleep

HEADER_LEN = 24 # (10,6,4,4)
RECV_BUFFER = 4096 + HEADER_LEN
PLAY_BUFFER = 32

# The Mad audio library we're using expects to be given a file object, but
# we're not dealing with files, we're reading audio data over the network.  We
# use this object to trick it.  All it really wants from the file object is the
# read() method, so we create this wrapper with a read() method for it to
# call, and it won't know the difference.
# NOTE: You probably don't need to modify this class.
# so we use mywrapper to wrap music data into file!
class mywrapper(object):
    def __init__(self):
        self.mf = None
        self.data = ""
        self.protocol = ""
        self.status = -1
        self.method = ""
        self.song_id = -1 # the id of the song currently playing
        self.new_data_added = False
        self.stop_requested = False

    # When it asks to read a specific size, give it that many bytes, and
    # update our remaining data.
    def read(self, size):
        result = self.data[:size]
        self.data = self.data[size:]
        return result


# Receive messages.  If they're responses to info/list, print
# the results for the user to see.  If they contain song data, the
# data needs to be added to the wrapper object.  Be sure to protect
# the wrapper with synchronization, since the other thread is using
# it too!
def recv_thread_func(wrap, cond_filled, sock):
    
    while True:
        cond_filled.acquire()
        # print  "recv_thread_func " + str(sock.getsockname()[1]) + " listening ... "
        message_received = sock.recv(RECV_BUFFER)
        # print ("message_format --> " + str(len(message_received)))
        message_length = len(message_received)
        message_format = ''
        if (message_length < (RECV_BUFFER)):
            # print "HELLO"
            message_format = '10sI4sI' + str(message_length-HEADER_LEN) + 's'
        else:
            message_format = '10sI4sI' + str(RECV_BUFFER-HEADER_LEN) + 's'

        # message_format = '10sI4sI' + str(RECV_BUFFER-HEADER_LEN) + 's'

        message_decoded = struct.unpack(message_format, message_received)      
        # sys.stderr.write(str(message_decoded) + "\n")

        wrap.protocol = message_decoded[0]
        wrap.status = message_decoded[1]
        wrap.method = message_decoded[2]
        requested_song = message_decoded[3]
        # message_size = message_decoded[4]

        if (wrap.method == 'EXIT'):
            print "from recv_thread_func: EXIT!"
            break
        elif (wrap.method == 'LIST'):
            sys.stderr.write(message_decoded[4])
        elif (wrap.method == 'PLAY'):
            if (wrap.status == 404 or wrap.status == 500):
                sys.stderr.write(message_decoded[4])

            elif (wrap.status == 200):
                # TODO
                if (wrap.song_id != requested_song):
                    wrap.data = ''
                    wrap.song_id = requested_song
                elif (wrap.song_id == requested_song):
                    sys.stderr.write("the song " + wrap.song_id + " is already playing")
                    pass

                wrap.data = wrap.data + message_decoded[4] #(add data to wrapper)
                wrap.new_data_added = True
                cond_filled.notify()
        elif (wrap.method == 'STOP'):
            wrap.data = ""
            sys.stderr.write(message_decoded[4])
            # wrap.stop_requested = True
            # cond_filled.notify()

        
        
        
        # if (message_decoded):
        #     #wrap.data = wrap.data + body_byte (add data to wrapper)
        #     cond_filled.notify()


        sys.stderr.flush()
        cond_filled.release() 
       


# If there is song data stored in the wrapper object, play it!
# Otherwise, wait until there is.  Be sure to protect your accesses
# to the wrapper with synchronization, since the other thread is
# using it too!
def play_thread_func(wrap, cond_filled, dev):
    while True:
        cond_filled.acquire()
        
        #while (not wrap.new_data_added):
        #    cond_filled.wait()
        while True:
            if wrap.new_data_added:
                break
            cond_filled.wait() # sleep until new data added
        
        # play the song, play just a lit bit each time!
        cond_filled.release() 
        print "play song!"

        wrap.mf = mad.MadFile(wrap)

        # Play the song, play what we have now.
        while True:
            buf = wrap.mf.read(PLAY_BUFFER)
            #print("buf is", buf)
            if buf is None:  # eof
                print "buf is None"
                break
            if wrap.method == 'STOP':
                break
            #print("length of buf is", len(buf))
            dev.play(buffer(buf), len(buf))

        #TODO
        # while True:
        #     buf = wrap.mf.read(RECV_BUFFER-HEADER_LEN)
        #     if (wrap.method=='STOP'):
        #            buf = None
        #     # example usage of dev and wrap (see mp3-example.py for a full example):
        #     if buf is None:  # eof
        #         break
        #     dev.play(buffer(buf), len(buf))
        
        wrap.new_data_added = False
        # wrap.stop_requested = False

        

        # print ("I got the song!")



def main():
    if len(sys.argv) < 3:
        print 'Usage: %s <server name/ip> <server port>' % sys.argv[0]
        sys.exit(1)

    # Create a pseudo-file wrapper, condition variable, and socket.  These will
    # be passed to the thread we're about to create.
    wrap = mywrapper()

    # Create a condition variable to synchronize the receiver and player threads.
    # In python, this implicitly creates a mutex lock too.
    # See: https://docs.python.org/2/library/threading.html#condition-objects
    cond_filled = threading.Condition()

    # Create a TCP socket and try connecting to the server.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((sys.argv[1], int(sys.argv[2])))

    # Create a thread whose job is to receive messages from the server.
    recv_thread = threading.Thread(
        target=recv_thread_func,
        args=(wrap, cond_filled, sock)
    )
    recv_thread.daemon = True
    recv_thread.start()

    # Create a thread whose job is to play audio file data.
    dev = ao.AudioDevice('pulse')
    play_thread = threading.Thread(
        target=play_thread_func,
        args=(wrap, cond_filled, dev)
    )
    play_thread.daemon = True
    play_thread.start()

    # Enter our never-ending user I/O loop.  Because we imported the readline
    # module above, raw_input gives us nice shell-like behavior (up-arrow to
    # go backwards, etc.).
    song_id = ''
    method = ''
    protocol = 'MyProtocol'
    data_to_send = None
    while True:
        # try:
            line = raw_input('>> ')

            if ' ' in line:
                cmd, args = line.split(' ', 1)
            else:
                cmd = line

            # TODO: Send messages to the server when the user types things.
            # if list, method is 'LIST'
            # if play, method is 'PLAY'
            # if stop, method is 'STOP'

            if cmd in ['l', 'list', 'L', 'LIST']:
                print 'The user asked for list.'
                method = 'LIST'
                data_to_send = struct.pack('4sI10s', method, 0, protocol)
                sock.send(data_to_send)
            elif cmd in ['p', 'play', 'P', 'PLAY']:
                print 'The user asked to play:', args
                method = 'PLAY'
                song_id = int(args)
                data_to_send = struct.pack('4sI10s', method, song_id, protocol)
                sock.send(data_to_send)
            elif cmd in ['s', 'stop', 'S', 'STOP']:
                print 'The user asked for stop.'
                method = 'STOP'
                data_to_send = struct.pack('4sI10s', method, 0, protocol)
                sock.send(data_to_send)
            # elif cmd in ['e', 'exit', 'E', 'EXIT']:
            #     print 'The user asked for exit (killing the client).'
            #     method = 'EXIT'
            #     data_to_send = struct.pack('4sI10s', method, 0, protocol)
            #     sock.send(data_to_send)

            if cmd in ['quit', 'q', 'exit']:
                sys.exit(0)

        # except (KeyboardInterrupt, SystemExit):
        #     print "main --> keyboardInterrupt"
        #     print 'The user asked for exit (killing the client).'
        #     method = 'EXIT'
        #     data_to_send = struct.pack('4sI10s', method, 0, protocol)
        #     sock.send(data_to_send)
        #     sys.exit(0)
        #     break



    sock.close()

if __name__ == '__main__':
    main()
