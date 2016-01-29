#!/bin/sh
. `dirname "$0"`/../config.sh
wget -nc -O /tmp/avsync.ts http://c3voc.mazdermind.de/testfiles/avsync.ts
(while true; do cat /tmp/avsync.ts || exit; done) | ffmpeg -y \
	-i - \
	-filter_complex "
		[0:v] scale=$WIDTH:$HEIGHT,fps=$FRAMERATE [v] ;
		[0:a] aresample=$AUDIORATE [a]
	" \
	-map "[v]" -map "[a]" \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:10000
