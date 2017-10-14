#!/bin/sh

# Best Practices: https://developers.facebook.com/docs/videos/live-video/best-practices/

# It may be possible to auto-gen the API key: https://developers.facebook.com/docs/graph-api/reference/live-video/
#   "You can make a POST request to live_videos edge from the following paths"

FACEBOOKURL="rtmp://live-api-a.facebook.com:80/rtmp/"
echo "Enter your Facebook Live Streaming Key"
read STREAMKEY

ffmpeg -y -nostdin \
	-thread_queue_size 512 \
	-timeout 3000000 \
	-i tcp://localhost:11000 \
	-t 14400 \		# Limit to 4 hour segment as Facebook API specifies
	-strict -2 \
	-c:a aac -ac 1 -ar 48000 -b:a 128k \ # 48Khz 128Kbps Mono
	-c:v libx264 \
	-preset medium \
	-pix_fmt yuv420p \
	-r 30 \
	-g 60 \ # Keyframe interval - every 2 seconds
	-vb 2048k -minrate 2000k -maxrate 4000k \
	-bufsize 4096k -threads 2  \
	-f flv 	"$FACEBOOKURL$STREAMKEY"

