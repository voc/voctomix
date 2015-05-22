#!/bin/bash

../voctocore.py -vv &
PID=$!
echo "PID=$PID"
sleep 1
./av-source-bmd-cam1.sh &
./av-source-bmd-cam2.sh &
./av-record-output-ffmpeg.sh &
#./av-stream-hd.sh &
demo-cycle-modes.sh
ffplay tcp://localhost:11000
kill $PID
wait
