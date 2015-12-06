#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=11000 !\
	matroskademux name=demux \
	\
	demux. !\
		queue !\
		videoconvert !\
		avenc_mpeg2video bitrate=5000000 max-key-interval=0 !\
		queue !\
		mux. \
	\
	demux. !\
		queue !\
		audioconvert !\
		avenc_mp2 bitrate=192000 !\
		queue !\
		mux. \
	\
	mpegtsmux name=mux !\
		filesink location=foo.ts
