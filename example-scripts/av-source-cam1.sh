#!/bin/sh
ffmpeg -y \
	-i "$HOME/31c3-sendezentrum-1013-de-Methodisch_inkorrekt_Die_falsche_42_hd.mp4" \
	-ac 2 \
	-af aresample=48000 \
	-pix_fmt uyvy422 \
	-c:v rawvideo \
	-c:a pcm_s16le \
	-f matroska \
	tcp://localhost:10000
