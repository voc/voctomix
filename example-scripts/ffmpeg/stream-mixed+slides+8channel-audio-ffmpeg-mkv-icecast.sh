#!/bin/sh
ffmpeg -y -nostdin -hide_banner \
	-thread_queue_size 512 -i tcp://localhost:15000?timeout=3000000 \
	-thread_queue_size 512 -i tcp://localhost:15001?timeout=3000000 \
	-filter_complex \
		"[0:v] hqdn3d [hd];
		[1:v] scale=1024:576, fps=5, hqdn3d [slides];
    [0]pan=stereo|c0=c0|c1=c1[a];
    [0]pan=stereo|c0=c2|c1=c3[b];
    [0]pan=stereo|c0=c4|c1=c5[c];
    [0]pan=stereo|c0=c6|c1=c7[d]" \
	-c:v libx264 -preset:v veryfast -profile:v main -pix_fmt yuv420p -flags +cgop \
	-threads:v 0 -aspect 16:9 \
	-map [hd] -metadata:s:v:0 title="HD" \
	-r:v:0 25 -g:v:0 75 -crf:v:0 21 -maxrate:v:0 4M -bufsize:v:0 18M \
	-map [slides] -metadata:s:v:1 title="Slides" \
	-g:v:1 15 -crf:v:1 25 -maxrate:v:1 100k -bufsize:v:1 750k \
	-c:a aac -b:a 192k -ar 48000 \
  -map "[a]" \
  -map "[b]" \
  -map "[c]" \
  -map "[d]" \
	-f matroska \
	-password password \
	-content_type video/webm \
	icecast://host:8000/mountpoint

