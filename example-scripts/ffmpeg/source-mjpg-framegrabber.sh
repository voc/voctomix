#!/bin/sh
. `dirname "$0"`/../config.sh
ffmpeg -y -nostdin -xerror \
	-timeout 3000000 -i "http://10.73.5.2:1881/stream.mjpg" \
	-filter_complex "
		[0:v] scale=$WIDTH:$HEIGHT,fps=$FRAMERATE [v] ;
		anullsrc=r=$AUDIORATE:cl=stereo [a]
	" \
	-map "[v]" -map "[a]" \
	-c:a pcm_s16le \
	-c:v rawvideo \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:10002
