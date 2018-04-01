#!/bin/bash

../../voctocore/voctocore.py -v &
PID=$!
echo "PID=$PID"
sleep 1
../ffmpeg/source-testvideo-as-cam1.sh >/dev/null 2>/dev/null &
../ffmpeg/source-testvideo-as-cam2.sh >/dev/null 2>/dev/null &
../ffmpeg/source-background-loop.sh &
#../ffmpeg/stream-hd.sh &
../ffmpeg/record-mixed-ffmpeg-segmented-timestamps.sh
../control-server/demo-cycle-modes.sh &
ffplay tcp://localhost:11000
kill $PID
wait
