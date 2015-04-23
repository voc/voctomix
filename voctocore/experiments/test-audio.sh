#!/bin/sh
gst-launch-1.0 audiotestsrc ! audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2 ! gdppay ! tcpclientsink host=localhost port=6000
