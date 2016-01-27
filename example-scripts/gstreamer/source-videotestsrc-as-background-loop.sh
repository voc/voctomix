#!/bin/sh
gst-launch-1.0 \
	videotestsrc pattern=smpte !\
		video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1 !\
		mux. \
	\
	matroskamux name=mux !\
		tcpclientsink host=localhost port=16000
