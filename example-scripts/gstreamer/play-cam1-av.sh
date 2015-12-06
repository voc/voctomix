#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13000 !\
	matroskademux name=demux \
	\
	demux. !\
		queue !\
		glupload !\
		glimagesink ts-offset=500000000 \
	\
	demux. !\
		queue !\
		alsasink provide-clock=false ts-offset=500000000
