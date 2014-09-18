#!/bin/sh
mkdir -p /tmp/voctomix-sockets/
rm -f /tmp/voctomix-sockets/v-cam2 /tmp/voctomix-sockets/a-cam2
gst-launch-1.0 -v \
	uridecodebin \
		uri=file:///home/peter/ED_1280.avi \
		name=src \
	\
	src. !\
	queue !\
	progressreport !\
	videoconvert !\
	videorate !\
	videoscale !\
	video/x-raw,format=RGBx,width=1280,height=720,framerate=25/1,pixel-aspect-ratio=1/1 !\
	gdppay !\
	shmsink \
		socket-path=/tmp/voctomix-sockets/v-cam2 \
		shm-size=100000000 \
	\
	src. !\
	queue !\
	audioresample !\
	audioconvert !\
	audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 !\
	gdppay !\
	shmsink \
		socket-path=/tmp/voctomix-sockets/a-cam2 \
		shm-size=10000000
