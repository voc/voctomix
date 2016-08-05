#!/bin/sh
confdir="`dirname "$0"`/../"
. $confdir/default-config.sh
if [ -f $confdir/config.sh ]; then
	. $confdir/config.sh
fi

workdir=`dirname "$0"`
$workdir/source-videotestsrc-as-background-loop.sh &
$workdir/source-videotestsrc-as-cam1.sh &
$workdir/source-videotestsrc-as-cam2.sh &
$workdir/source-videotestsrc-as-grabber.sh &

wait
