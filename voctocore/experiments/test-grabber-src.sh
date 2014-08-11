#!/bin/sh
gst-launch-1.0 -vm \
	videotestsrc !\
	video/x-raw,width=1280,height=720,framerate=25/1,format=BGRA !\
	queue !\
	shmsink \
		sync=true \
		socket-path=/tmp/grabber \
		wait-for-connection=false \
		shm-size=100000000
