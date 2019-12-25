#!/bin/sh

ffmpeg -v verbose -nostats -y -analyzeduration 10000 \
        -thread_queue_size 512 -i tcp://localhost:11000?timeout=3000000 \
        -thread_queue_size 512 -i tcp://localhost:13003?timeout=3000000 \
        -aspect 16:9 \
        -filter_complex \
          "[0]pan=stereo|c0=c0|c1=c1[a];
           [0]pan=stereo|c0=c2|c1=c3[b];
           [0]pan=stereo|c0=c4|c1=c5[c];
           [0]pan=stereo|c0=c6|c1=c7[d]" \
           -map 0:v -c:v:0 mpeg2video -pix_fmt:v:0 yuv420p -qscale:v:0 4 -qmin:v:0 4 -qmax:v:0 4 -keyint_min:v:0 5 -bf:v:0 0 -g:v:0 5 -me_method:v:0 dia \
           -map 1:v -c:v:1 mpeg2video -pix_fmt:v:1 yuv420p -qscale:v:1 4 -qmin:v:1 4 -qmax:v:1 4 -keyint_min:v:1 5 -bf:v:1 0 -g:v:1 5 -me_method:v:1 dia \
           -map "[a]" -c:a s302m \
           -map "[b]" -c:a s302m \
           -map "[c]" -c:a s302m \
           -map "[d]" -c:a s302m \
        -flags +global_header \
        -strict -2 \
        -f segment -segment_time 180 -strftime 1 -segment_format mpegts "segment-%Y-%m-%d_%H-%M-%S-$$.ts"

