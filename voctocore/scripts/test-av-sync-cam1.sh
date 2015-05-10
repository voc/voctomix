#!/bin/sh
gst-launch-1.0 -vm \
	uridecodebin \
		uri=http://c3voc.mazdermind.de/avsync.mp4 \
		name=src \
	\
	src. !\
	queue !\
	videoconvert !\
	videoscale !\
	video/x-raw,format=I420,width=1280,height=720,framerate=25/1,pixel-aspect-ratio=1/1 ! \
	timeoverlay valignment=bottom ! \
	gdppay ! \
	tcpclientsink host=localhost port=10000 \
	\
	src. !\
	queue !\
	audioconvert !\
	audioresample !\
	audiorate !\
	audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
	gdppay !\
	tcpclientsink host=localhost port=20000
