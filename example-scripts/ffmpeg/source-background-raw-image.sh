#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

# This script is an example how a static raw image as Background-Loop can be
# looped into voctomix as a background. This approach consumes much less CPU
# the the mpeg-ts based source-scripts.
#
# To generate the required "background.raw" the following command can be used:
#
# ffmpeg \
#   -i background.png \
#   -c:v rawvideo \
#   -pix_fmt:v yuv420p \
#   -frames 1 \
#   -f rawvideo \
#   background.raw

ffmpeg -re -y -f image2 -loop 1 -pixel_format yuv420p \
	-framerate ${FRAMERATE} -video_size ${WIDTH}x${HEIGHT} \
	-i background.raw \
	-c:v rawvideo -pix_fmt yuv420p \
	-f matroska \
	tcp://localhost:16000
