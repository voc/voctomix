#!/bin/sh
ffmpeg -y \
	-f decklink \
	-i 'DeckLink Mini Recorder (2)@11' \
	-c:v rawvideo -c:a pcm_s16le \
        -pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:10001
