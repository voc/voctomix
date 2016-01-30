#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=11000 !\
	matroskademux !\
	glupload !\
	glimagesink ts-offset=500000000
