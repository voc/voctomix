#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=11000 !\
	matroskademux !\
	xvimagesink
