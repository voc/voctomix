#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

wget -nc -O /tmp/machine_lullaby_1.ogg http://c3voc.mazdermind.de/testfiles/machine_lullaby_1.ogg
while true; do
	ffmpeg -y -nostdin \
		-i "/tmp/machine_lullaby_1.ogg" \
		-ac 2 \
		-af aresample=$AUDIORATE \
		-c:a pcm_s16le \
		-f matroska \
		tcp://localhost:18000

	sleep 1;
done
