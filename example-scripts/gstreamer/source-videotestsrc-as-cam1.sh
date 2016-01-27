#!/bin/sh
gst-launch-1.0 \
	videotestsrc pattern=ball foreground-color=0x00ff0000 background-color=0x00440000 !\
		video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1 !\
		mux. \
	\
	audiotestsrc freq=440 !\
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
		mux. \
	\
	matroskamux name=mux !\
		tcpclientsink host=localhost port=10000
