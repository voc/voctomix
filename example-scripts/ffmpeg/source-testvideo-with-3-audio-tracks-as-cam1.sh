#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

ffmpeg -ss 293 -y -nostdin \
	-i "http://cdn.media.ccc.de/congress/2016/h264-hd/33c3-8429-eng-deu-fra-33C3_Opening_Ceremony_hd.mp4" \
	-ac 2 \
	-filter_complex "
		[0:v] scale=$WIDTH:$HEIGHT,fps=$FRAMERATE [v]
	" \
	-map "[v]" -map "0:a:0" -map "0:a:1" -map "0:a:2" \
	-pix_fmt yuv420p \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-f matroska \
	tcp://localhost:10000
