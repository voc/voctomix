#!/bin/sh
gst-launch-1.0 -vm \
	videotestsrc pattern=ball background-color=0x00ff00ff !\
	video/x-raw,width=1280,height=720,framerate=25/1,format=RGBx !\
	progressreport update-freq=1 !\
	queue !\
	shmsink \
		sync=true \
		socket-path=/tmp/v-cam2 \
		wait-for-connection=false \
		shm-size=100000000
