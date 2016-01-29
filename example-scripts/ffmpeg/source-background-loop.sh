#!/bin/sh
. `dirname "$0"`/../config.sh
wget -nc -O /tmp/bg.ts http://c3voc.mazdermind.de/testfiles/bg.ts
while true; do cat /tmp/bg.ts || exit 1; done |\
	ffmpeg -re -i - \
	-filter_complex "
		[0:v] scale=$WIDTH:$HEIGHT,fps=$FRAMERATE [v]
	" \
	-map "[v]" \
	-c:v rawvideo \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:16000
