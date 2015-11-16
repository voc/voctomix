#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=13001 !\
	matroskademux !\
	alsasink
