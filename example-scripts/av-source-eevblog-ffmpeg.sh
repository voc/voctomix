#!/bin/sh
ffmpeg -y \
	-i $HOME/eevblog.mp4 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-pix_fmt uyvy422 \
	-af aresample=48000 \
	-f matroska \
	tcp://localhost:10000
