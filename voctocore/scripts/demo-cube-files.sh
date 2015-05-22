#!/bin/bash

../voctocore.py -vv &
PID=$!
echo "PID=$PID"
sleep 1
./av-source-cam1.sh &
./av-source-cam2.sh &
./av-record-output-ffmpeg-timestamps.sh &
./av-stream-hd.sh &
./demo-cycle-modes.sh &
while true; do sleep 1; done
kill $PID
wait
