#!/bin/sh
gst-launch-1.0 \
	audiotestsrc !\
	audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
	gdppay !\
	tcpclientsink host=localhost port=20000
