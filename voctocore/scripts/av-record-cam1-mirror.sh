#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13000 !\
	matroskademux name=demux \
	\
	demux. !\
		queue !\
		textoverlay halignment=left valignment=top ypad=250 text=Recording !\
		timeoverlay halignment=left valignment=top ypad=250 xpad=400 !\
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
