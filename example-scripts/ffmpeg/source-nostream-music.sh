#!/bin/sh
wget -nc -O /tmp/machine_lullaby_1.ogg http://c3voc.mazdermind.de/testfiles/machine_lullaby_1.ogg
while true; do
	ffmpeg -y \
		-i "/tmp/machine_lullaby_1.ogg" \
		-ac 2 \
		-af aresample=48000 \
		-c:a pcm_s16le \
		-f matroska \
		tcp://localhost:18000
done
