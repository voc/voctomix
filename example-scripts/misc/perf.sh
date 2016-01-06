#!/bin/bash

../../voctocore/voctocore.py &
PID=$!
echo "PID=$PID"
sleep 1
../control-server/set-composite-side-by-side-equal.sh >/dev/null 2>/dev/null
../gstreamer/source-videotestsrc-as-cam1.sh >/dev/null 2>/dev/null &
../gstreamer/source-videotestsrc-as-cam2.sh >/dev/null 2>/dev/null &
../gstreamer/source-videotestsrc-as-grabber.sh >/dev/null 2>/dev/null &
../gstreamer/source-videotestsrc-as-background-loop.sh >/dev/null 2>/dev/null &
sudo perf top -g -p $PID
kill $PID
wait
