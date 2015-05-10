#!/bin/sh
gst-launch-1.0 videotestsrc ! video/x-raw,height=600,width=800,format=I420,framerate=25/1 ! timeoverlay valignment=bottom ! gdppay ! tcpclientsink host=localhost port=5000
