#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

gst-launch-1.0 \
	uridecodebin \
		uri=http://c3voc.mazdermind.de/testfiles/avsync.mp4 \
		name=src \
	\
	src. !\
		queue !\
		videoconvert !\
		videoscale !\
		video/x-raw,format=I420,width=$WIDTH,height=$HEIGHT,framerate=$FRAMERATE/1,pixel-aspect-ratio=1/1 ! \
		mux. \
	\
	src. !\
		queue !\
		audioconvert !\
		audioresample !\
		audiorate !\
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=$AUDIORATE !\
		mux. \
	\
	matroskamux name=mux !\
		tcpclientsink host=localhost port=10000
