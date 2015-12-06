#!/bin/sh
gst-launch-1.0 \
	videotestsrc pattern=ball !\
	video/x-raw,format=UYVY,width=1280,height=720,framerate=25/1,pixel-aspect-ratio=1/1 !\
	matroskamux !\
	tcpclientsink host=localhost port=16000
