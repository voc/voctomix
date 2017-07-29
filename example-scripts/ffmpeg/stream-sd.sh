#!/bin/sh
wget -nc -O /tmp/overlay_hd.png http://c3voc.mazdermind.de/testfiles/overlay_hd.png
ffmpeg -y -nostdin \
	-i tcp://localhost:15000 \
	-threads:0 0 \
	-aspect 16:9 \
	-c:v libx264 \
	-filter_complex '
		[0:v] yadif=mode=2, hqdn3d, scale=720:576 [deinter];
		movie=/tmp/overlay_hd.png [logo];
		[deinter] [logo] overlay=0:0 [out]
	' \
	-map '[out]' \
	-maxrate:v:0 800k -bufsize:v:0 8192k -crf:0 18 \
	-pix_fmt:0 yuv420p -profile:v:0 main -g:v:0 25 \
	-preset:v:0 veryfast \
	\
	-ac 1 -c:a libfdk_aac -b:a 96k -ar 44100 \
	-map 0:a -filter:a:0 pan=mono:c0=FL \
	-ac:a:2 2 \
	\
	-y -f flv rtmp://127.0.0.1:1935/stream/voctomix_hd
