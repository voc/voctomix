#!/bin/bash

../../voctocore/voctocore.py &
PID=$!
echo "PID=$PID"
sleep 1
../control-server/set-composite-side-by-side-equal.sh >/dev/null 2>/dev/null
../ffmpeg/source-testvideo-as-cam1.sh >/dev/null 2>/dev/null &
../ffmpeg/source-testvideo-as-cam2.sh >/dev/null 2>/dev/null &
pidstat -p $PID 1 &
sleep 10
kill $PID
wait
