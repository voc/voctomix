#!/bin/sh
wget -nc -O /tmp/pause.ts http://c3voc.mazdermind.de/testfiles/pause.ts
while true; do cat /tmp/pause.ts || exit 1; done |\
	ffmpeg -re -i - \
	-map 0:v \
	-c:v rawvideo \
	-pix_fmt uyvy422 \
	-f matroska \
	tcp://localhost:17000
