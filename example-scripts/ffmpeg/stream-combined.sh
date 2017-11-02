#!/bin/sh

#
# a variation of this script was used to generate all combinations of
# [native|translated|stereo]_[hd|sd|slides] streams for 33c3
#

ffmpeg -y -nostdin \
	-thread_queue_size 512 \
	-i tcp://localhost:15000 \
	-thread_queue_size 512 \
	-i tcp://localhost:13000 \
	-threads:0 0 \
	-aspect 16:9 \
	-filter_complex '
		[0:v] yadif=mode=2, hqdn3d, split [deinter_hd] [deinter_hd2];
		[deinter_hd2] scale=720:576 [deinter_sd];
		[1:v] scale=720:576, fps=5, hqdn3d [deinter_slides];
		movie=/opt/voc/share/overlay_hd.png [logo_hd];
		[deinter_hd] [logo_hd] overlay=0:0 [hd];
		movie=/opt/voc/share/overlay_sd.png [logo_sd];
		[deinter_sd] [logo_sd] overlay=0:0 [sd];
		movie=/opt/voc/share/overlay_slides.png [logo_slides];
		[deinter_slides] [logo_slides] overlay=0:0 [slides]
	' \
	-map '[hd]' -map '[sd]' -map '[slides]' \
	\
	-maxrate:v:0 3000k -crf:0 21 \
	-maxrate:v:1 800k  -crf:1 18 \
	-maxrate:v:2 100k  -crf:2 25 \
	\
	-c:v:0 libx264 -preset:v:0 veryfast -bufsize:v:0 8192k -pix_fmt:0 yuv420p -profile:v:0 main \
	-c:v:1 libx264 -preset:v:0 veryfast -bufsize:v:1 8192k -pix_fmt:1 yuv420p -profile:v:1 main \
	-c:v:2 libx264 -preset:v:0 veryfast -bufsize:v:2 8192k -pix_fmt:2 yuv420p -profile:v:2 main \
	\
	-g:v:0 25 \
	-g:v:1 25 \
	-g:v:2 50 \
	\
	-map 0:a:0 -filter:a:0 pan='mono|c0=FL' \
	-c:a:0 aac -b:a:0 96k -ar 44100 \
	\
	-map 0:a:0 -filter:a:1 pan='mono|c0=FR' \
	-c:a:1 aac -b:a:1 96k -ar 44100 \
	\
	-map 0:a:0 \
	-c:a:2 aac -b:a:2 96k -ar 44100 \
	\
	-max_interleave_delta 0 \
	-f nut pipe: | \
		ffmpeg -v warning -y -nostdin -f nut -i pipe: \
			\
			-c:v copy -c:a copy \
			-map 0:v:0 -map 0:a:0 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_native_hd \
			\
			-c:v copy -c:a copy \
			-map 0:v:0 -map 0:a:1 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_translated_hd \
			\
			-c:v copy -c:a copy \
			-map 0:v:0 -map 0:a:2 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_stereo_hd \
			\
			\
			-c:v copy -c:a copy \
			-map 0:v:1 -map 0:a:0 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_native_sd \
			\
			-c:v copy -c:a copy \
			-map 0:v:1 -map 0:a:1 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_translated_sd \
			\
			-c:v copy -c:a copy \
			-map 0:v:1 -map 0:a:2 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_stereo_sd \
			\
			\
			-c:v copy -c:a copy \
			-map 0:v:2 -map 0:a:0 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_native_slides \
			\
			-c:v copy -c:a copy \
			-map 0:v:2 -map 0:a:1 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_translated_slides \
			\
			-c:v copy -c:a copy \
			-map 0:v:2 -map 0:a:2 \
			-f flv rtmp://127.0.0.1:1935/stream/stream_stereo_slides
