#!/bin/sh
gst-launch-1.0 -vm \
	videotestsrc pattern=ball !\
	video/x-raw,width=1280,height=720,framerate=25/1,format=RGBx !\
	queue !\
	shmsink \
		sync=true \
		socket-path=/tmp/voctomix-sockets/v-cam1 \
		wait-for-connection=false \
		shm-size=100000000
