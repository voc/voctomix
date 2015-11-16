#!/bin/sh
ffmpeg -i tcp://localhost:11000 -aspect 16:9 -threads:0 0 \
-c:v libx264 \
-filter_complex "
  yadif=mode=2, hqdn3d [deinter];
  movie=$HOME/overlay_hd.png [logo];
  [deinter] [logo] overlay=0:0 [out]
" -map '[out]' -maxrate:v:0 3000k -bufsize:v:0 8192k -crf:0 21 -pix_fmt:0 yuv420p -profile:v:0 main -g:v:0 25 -preset:v:0 veryfast \
-ac 1 -c:a libfdk_aac -b:a 96k -ar 44100 \
-map 0:a -filter:a:0 pan=mono:c0=FL \
-ac:a:2 2 \
-y -f flv rtmp://127.0.0.1:1935/stream/voctomix
