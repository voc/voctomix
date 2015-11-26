#!/bin/sh
ffmpeg -y \
	-i "http://10.73.5.2:1881/stream.mjpg" \
	-filter_complex " [0:v] scale=1920:1080,fps=25 [v] ; anullsrc=r=48000:cl=stereo [a] " \
	-map "[v]" \
	-map "[a]" \
	-c:a pcm_s16le \
	-c:v rawvideo \
	-f matroska \
	tcp://localhost:10002
