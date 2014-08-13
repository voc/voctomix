#!/bin/sh
gst-launch-1.0 -v \
	uridecodebin \
		uri=http://video.blendertestbuilds.de/download.blender.org/ED/ED_1280.avi \
		name=src \
	\
	src. !\
	queue !\
	progressreport !\
	videoconvert !\
	videorate !\
	videoscale !\
	video/x-raw,format=BGRA,width=1280,height=720,framerate=25/1 !\
	shmsink \
		sync=true \
		socket-path=/tmp/grabber-v \
		wait-for-connection=false \
		shm-size=100000000
	\
	src. !\
	queue !\
	audioconvert !\
	audiorate !\
	audio/x-raw,format=S16LE,layout=interleaved,rate=44100,channels=2 !\
	shmsink \
		sync=true \
		socket-path=/tmp/grabber-a \
		wait-for-connection=false \
		shm-size=10000000
