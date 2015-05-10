#!/bin/sh
gst-launch-1.0 \
	videotestsrc !\
	video/x-raw,format=I420,width=1280,height=720,framerate=25/1,pixel-aspect-ratio=1/1 !\
	timeoverlay valignment=bottom !\
	gdppay !\
	tcpclientsink host=localhost port=10000
