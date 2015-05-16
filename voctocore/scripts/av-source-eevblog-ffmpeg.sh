#!/bin/sh
ffmpeg -y \
	-i $HOME/eevblog.mp4 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-af aresample=48000 \
	-f matroska \
	tcp://localhost:10000
