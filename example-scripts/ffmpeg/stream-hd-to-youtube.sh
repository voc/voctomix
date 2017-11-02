#!/bin/sh
wget -nc -O /tmp/overlay_hd.png http://c3voc.mazdermind.de/testfiles/overlay_hd.png
ffmpeg -y -nostdin \
	-i tcp://localhost:15000 \
	-threads:0 0 \
	-aspect 16:9 \
	-c:v libx264 \
	-filter_complex '
		[0:v] yadif=mode=2, hqdn3d [deinter];
		movie=/tmp/overlay_hd.png [logo];
		[deinter] [logo] overlay=0:0 [out]
	' \
	-map '[out]' \
	-maxrate:v:0 3000k -bufsize:v:0 8192k -crf:0 21 \
	-pix_fmt:0 yuv420p -profile:v:0 main -g:v:0 25 \
	-preset:v:0 veryfast \
	\
	-ac 1 -c:a aac -b:a 96k -ar 44100 \
	-map 0:a -filter:a:0 pan=mono:c0=FL \
	-ac:a:2 2 \
	\
	-y -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
