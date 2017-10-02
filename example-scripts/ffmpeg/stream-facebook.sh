#!/bin/sh

# Go to Facebook.com, and start a new "Live Video" post
# At the top of the video window, select "Connect" instead of "Camera"
# Enter the API key below to start the stream
FACEBOOKURL="rtmp://live-api-a.facebook.com:80/rtmp/"
STREAMKEY="<STREAMKEY>"

ffmpeg -y -nostdin \
	-thread_queue_size 512 \
	-timeout 3000000 \
	-i tcp://localhost:11000 \
	-t 5400 \
	-strict -2 \
	-c:a aac -ac 1 -ar 44100 -b:a 128k \
	-c:v libx264 \
	-preset superfast \
	-pix_fmt yuv420p \
	-r 30 \
	-g 60 \
	-vb 2048k -minrate 2000k -maxrate 4000k \
	-bufsize 4096k -threads 2  \
	-f flv 	"$FACEBOOKURL$STREAMKEY"

