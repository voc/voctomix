#!/bin/sh
ffmpeg -y \
	-i http://c3voc.mazdermind.de/testfiles/avsync.ts \
	-vf scale=1920x1080 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:10000
