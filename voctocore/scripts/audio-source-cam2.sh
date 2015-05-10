#!/bin/sh
gst-launch-1.0 \
	audiotestsrc freq=330 !\
	audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
	gdppay !\
	tcpclientsink host=localhost port=20001
