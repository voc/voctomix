#!/bin/bash

../voctocore.py -vv &
PID=$!
echo "PID=$PID"
sleep 1
./set-composite-side-by-side-equal.sh
./av-source-cam1.sh &
./av-source-cam2.sh &
./av-record-output-ffmpeg-timestamps.sh &
./av-stream-hd.sh &
while true; do sleep 1; done
kill $PID
wait
