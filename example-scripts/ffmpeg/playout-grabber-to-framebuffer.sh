#!/bin/sh
fbset -g 1920 1080 1920 1080 32
echo 0 >/sys/class/graphics/fbcon/cursor_blink

ffmpeg \
	-i tcp://localhost:13002 \
	-map 0:v \
	-c:v rawvideo \
	-pix_fmt bgra \
	-f fbdev /dev/fb0
