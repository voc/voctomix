#!/bin/sh
rm -f /tmp/voctomix-sockets/v-cam2 /tmp/voctomix-sockets/a-cam2
gst-launch-1.0 -v \
	uridecodebin \
		uri=file:///home/peter/Sintel.2010.720p.mkv \
		name=src \
	\
	src. !\
	queue !\
	progressreport !\
	videoconvert !\
	videorate !\
	videoscale !\
	video/x-raw,format=RGBx,width=1280,height=720,framerate=25/1 !\
	shmsink \
		sync=true \
		socket-path=/tmp/voctomix-sockets/v-cam2 \
		wait-for-connection=false \
		shm-size=100000000 \
	\
	src. !\
	queue !\
	audioconvert !\
	audiorate !\
	audio/x-raw,format=F32LE,layout=interleaved,channels=2,rate=48000 !\
	shmsink \
		sync=true \
		socket-path=/tmp/voctomix-sockets/a-cam2 \
		wait-for-connection=false \
		shm-size=10000000
