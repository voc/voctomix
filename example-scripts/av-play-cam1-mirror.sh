#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13000 !\
	matroskademux name=demux \
	\
	demux. !\
	queue !\
	xvimagesink ts-offset=300000000 \
	\
	demux. !\
	queue !\
	alsasink provide-clock=false ts-offset=300000000
