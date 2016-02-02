#!/bin/sh
ffmpeg -y -nostdin \
	-f decklink \
	-i 'DeckLink Mini Recorder (2)@10' \
	-c:v rawvideo -c:a pcm_s16le \
	-pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:10001
