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
	video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! \
	timeoverlay valignment=bottom ! \
	gdppay ! \
	tcpclientsink host=localhost port=5000 \
	\
	src. !\
	queue !\
	audioconvert !\
	audioresample !\
	audiorate !\
	audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 !\
	gdppay !\
	tcpclientsink host=localhost port=6000
