#!/bin/sh
. `dirname "$0"`/../config.sh
gst-launch-1.0 \
	videotestsrc pattern=ball foreground-color=0x0000ff00 background-color=0x00004400 !\
		video/x-raw,format=UYVY,width=$WIDTH,height=$HEIGHT,framerate=$FRAMERATE/1,pixel-aspect-ratio=1/1 ! \
		mux. \
	\
	audiotestsrc freq=550 !\
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=$AUDIORATE !\
		mux. \
	\
	matroskamux name=mux !\
		tcpclientsink host=localhost port=10001
