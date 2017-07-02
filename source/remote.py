import sys
import os
import shlex
import time
import functions
import asyncio
import websockets
import subprocess
from threading import Thread

# Export mouse x and y, and keyboard button press status
left_mouse_down = False
right_mouse_down = False
x = 0
y = 0
left = False
right = False
up = False
down = False

# Finished?
done = False

# Start thread and create new event loop
loop = asyncio.new_event_loop()
def thread_function(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
thread = Thread(target=thread_function, args=(loop,))
thread.start()    

# Coroutine for websocket handling
@asyncio.coroutine
def remote_connect():
    global x, y, left_mouse_down, right_mouse_down, left, right, up, down
    try:
        websocket = yield from websockets.connect("ws://meetzippy.com:8080")
        print( "Connected to server." )
    except:
        print( "No meetzippy.com connection." )
        return

    # Loop
    try:
        while not done:
            text = yield from websocket.recv()
            if text.startswith( 'left' ):
                print( text )
                left = (len(text.split()) > 1 and text.split()[1] == "down")
                print( left )
            elif text.startswith( 'right' ):
                right = (len(text.split()) > 1 and text.split()[1] == "down")
            elif text.startswith( 'up' ):
                up = (len(text.split()) > 1 and text.split()[1] == "down")
            elif text.startswith( 'down' ):
                down = (len(text.split()) > 1 and text.split()[1] == "down")
            elif text.startswith( 'x' ):
                x = int(text.split()[1])
            elif text.startswith( 'y' ):
                y = int(text.split()[1])
            elif text.startswith( 'left_mouse' ):
                left_mouse_down = (len(text.split()) > 1 and text.split()[1] == "down")
            elif text.startswith( 'right_mouse' ):
                right_mouse_down = (len(test.split()) > 1 and text.split()[1] == "down")
    finally:
        yield from websocket.close()
    print( "Remote done" )

# Run coroutine to listen for keyboard/mouse remote commands via websocket
loop.call_soon_threadsafe(asyncio.async, remote_connect())


# Start video transmission
def video_function():
    # Wake up raspi camera
    os.system("sudo modprobe bcm2835-v4l2")

	# Set camera params
    os.system("v4l2-ctl -c brightness={brightness} -c contrast={contrast} -c saturation={saturation}".format(brightness = 70,
                                                                                                             contrast = 70,
                                                                                                             saturation = 70))
	# Stop ffmpeg
    os.system("sudo killall -9 ffmpeg 2> /dev/null")

    # Start ffmpeg
    commandLine = 'ffmpeg -loglevel error -f alsa -ar 44100 -ac 1 -i hw:1 -f mpegts -codec:a mp2 -f v4l2 -framerate 30 -video_size 640x480 -i /dev/video0 -f mpegts -codec:v mpeg1video -s 640x480 -b:v 200k -bf 0 -muxdelay 0.001 http://meetzippy.com:8081/supersecret'
    ffmpegProcess = subprocess.Popen(shlex.split(commandLine))    
    print( "Started ffmpeg" )

# Start thread
thread = Thread(target=video_function, args=())
thread.start()    

#try:
#	import thread
#	thread.start_new_thread( remote_listener, () )
#except:
#	print( "Error: Cannot start remote listener. Please install python threads." )
