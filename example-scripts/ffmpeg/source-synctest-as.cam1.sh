#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

ffmpeg  -y -nostdin \
	-re -f lavfi -i "testsrc=s=${WIDTH}x${HEIGHT}:r=${FRAMERATE}:n=3[out0];sine=r=${AUDIORATE}:beep_factor=1:f=1000[out1]" \
	-pix_fmt yuv420p \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-f matroska \
	tcp://localhost:10000
