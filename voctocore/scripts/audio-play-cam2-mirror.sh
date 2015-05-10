#!/bin/sh
gst-launch-1.0 \
	tcpclientsrc host=localhost port=23001 !\
	gdpdepay !\
	alsasink sync=false
