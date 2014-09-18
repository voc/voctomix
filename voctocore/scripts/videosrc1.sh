#!/bin/sh
mkdir -p /tmp/voctomix-sockets/
rm -f /tmp/voctomix-sockets/v-cam1 /tmp/voctomix-sockets/a-cam1
gst-launch-1.0 -v \
	uridecodebin \
		uri=file:///home/peter/avsync.mp4 \
		name=src \
	\
	src. !\
	queue !\
	progressreport !\
	videoconvert !\
	videorate !\
	videoscale !\
	video/x-raw,format=RGBx,width=1280,height=720,framerate=25/1 !\
	gdppay !\
	shmsink \
		socket-path=/tmp/voctomix-sockets/v-cam1 \
		shm-size=100000000 \
	\
	src. !\
	queue !\
	audioresample !\
	audioconvert !\
	audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 !\
	gdppay !\
	shmsink \
		socket-path=/tmp/voctomix-sockets/a-cam1 \
		shm-size=10000000

