#!/bin/sh
gst-launch-1.0 -vm \
	filesrc location=$HOME/eevblog.mp4 !\
	decodebin name=src \
	\
	src. !\
		queue !\
		videoconvert !\
		videoscale !\
		video/x-raw,format=I420,width=1280,height=720,framerate=25/1,pixel-aspect-ratio=1/1 ! \
		textoverlay halignment=left valignment=top ypad=300 text=Playback !\
		timeoverlay halignment=left valignment=top ypad=300 xpad=400 !\
		mux. \
	\
	src. !\
		queue !\
		audioconvert !\
		audioresample !\
		audiorate !\
		audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000 !\
		mux. \
	\
	matroskamux name=mux !\
	tcpclientsink host=localhost port=10000
