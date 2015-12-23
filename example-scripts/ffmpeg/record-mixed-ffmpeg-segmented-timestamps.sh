#!/bin/sh

# WARNING: Using '%t' in the output filename requires a patched FFmpeg!
# If this command fails with the message 'Invalid segment filename template',
# you do not have such a FFmpeg version.

ffmpeg \
	-i tcp://localhost:11000 \
	-ac 2 -channel_layout 2 -aspect 16:9 \
	-map 0:v -c:v:0 mpeg2video -pix_fmt:v:0 yuv422p -qscale:v:0 2 -qmin:v:0 2 -qmax:v:0 7 -keyint_min 0 -bf:0 0 -g:0 0 -intra:0 -maxrate:0 90M \
	-map 0:a -c:a:0 mp2 -b:a:0 192k -ac:a:0 2 -ar:a:0 48000 \
	-flags +global_header -flags +ilme+ildct \
	-f segment -segment_time 180 -segment_format mpegts segment-%t-%05d.ts
