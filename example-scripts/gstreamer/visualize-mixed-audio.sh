#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13000 !\
	matroskademux !\
	audioconvert !\
	wavescope shader=none style=lines !\
	video/x-raw,width=800,height=300 !\
	glupload !\
	glimagesink
