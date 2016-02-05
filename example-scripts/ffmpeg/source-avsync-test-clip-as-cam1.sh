#!/bin/sh
. `dirname "$0"`/../config.sh
ffmpeg -y -nostdin \
	-i http://c3voc.mazdermind.de/testfiles/avsync.ts \
	-filter_complex "
		[0:v] scale=$WIDTH:$HEIGHT,fps=$FRAMERATE [v] ;
		[0:a] aresample=$AUDIORATE [a]
	" \
	-map "[v]" -map "[a]" \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-pix_fmt uyvy422 \
	-f matroska \
	tcp://localhost:10000
