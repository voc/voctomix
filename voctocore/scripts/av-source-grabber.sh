#!/bin/sh
ffmpeg -y \
	-i "http://10.73.5.2:1881/stream.mjpg" \
	-filter_complex "scale=1920:1080,fps=25" \
	-ar 48000 \
	-ac 2 \
	-f s16le \
	-i "/dev/zero" \
	-c:a pcm_s16le \
	-c:v rawvideo \
	-f matroska \
	tcp://localhost:10002
