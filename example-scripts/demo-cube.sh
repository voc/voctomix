#!/bin/bash

../voctocore.py -vv &
PID=$!
echo "PID=$PID"
sleep 1
./av-source-bmd-cam1.sh &
./av-source-bmd-cam2.sh &
./av-source-background-loop.py &
./av-record-output-ffmpeg-timestamps.sh &
./av-stream-hd.sh &
./demo-cycle-modes.sh &
while true; do sleep 1; done
kill $PID
wait
