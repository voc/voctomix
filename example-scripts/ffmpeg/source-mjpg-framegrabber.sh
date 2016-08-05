#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

ffmpeg -y -nostdin -xerror \
	-use_wallclock_as_timestamps 1 -timeout 3000000 -f mjpeg -i "http://10.73.5.2:1881/stream.mjpg" \
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
