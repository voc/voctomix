#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13000 !\
		gdpdepay !\
		queue !\
		timeoverlay !\
		videoconvert !\
		avenc_mpeg2video bitrate=5000000 max-key-interval=0 !\
		queue !\
		mux. \
	\
	tcpclientsrc host=localhost port=23000 !\
		gdpdepay !\
		queue !\
		avenc_mp2 bitrate=192000 !\
		queue !\
		mux. \
	\
	mpegtsmux name=mux !\
		filesink location=foo.ts
