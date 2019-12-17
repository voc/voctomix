#!/bin/sh
ffmpeg -y -nostdin -hide_banner \
  -init_hw_device vaapi=foo:/dev/dri/renderD128 \
  -hwaccel vaapi \
  -hwaccel_output_format vaapi \
  -hwaccel_device foo \
  -thread_queue_size 1024 -i tcp://localhost:15000?timeout=3000000 \
  -thread_queue_size 1024 -i tcp://localhost:15001?timeout=3000000 \
  -filter_hw_device foo \
  -filter_complex \
  "[0:v] hqdn3d, format=nv12,hwupload [hd];
	[1:v] fps=5, hqdn3d, format=nv12,hwupload,scale_vaapi=w=1024:h=576 [slides];
  [0]pan=stereo|c0=c0|c1=c1[a];
  [0]pan=stereo|c0=c2|c1=c3[b];
  [0]pan=stereo|c0=c4|c1=c5[c];
  [0]pan=stereo|c0=c6|c1=c7[d]" \
  -map [hd]  -metadata:s:v:0 title="HD" \
  -map [slides] -metadata:s:v:1 title="Slides" \
  -map "[a]" \
  -map "[b]" \
  -map "[c]" \
  -map "[d]" \
  -c:v h264_vaapi -flags +cgop -aspect 16:9 -g:v:1 15 -crf:v:1 25 -maxrate:v:1 100k -bufsize:v:1 750k -r:v:0 25 -g:v:0 75 -crf:v:0 21 -maxrate:v:0 4M -bufsize:v:0 18M\
  -c:a aac -b:a 192k -ar 48000 \
  -f matroska \
  -password password \
  -content_type video/webm \
  icecast://host:8000/mountpoint

