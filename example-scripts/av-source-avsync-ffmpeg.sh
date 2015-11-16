#!/bin/sh
(while true; do cat $HOME/avsync.ts || exit; done) | ffmpeg -y \
	-i - \
	-vf scale=1920x1080 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-f matroska \
	tcp://localhost:10000
