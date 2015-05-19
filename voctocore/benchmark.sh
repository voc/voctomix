#!/bin/bash

./voctocore.py &
PID=$!
echo "PID=$PID"
sleep 1
./scripts/set-composite-side-by-side-equal.sh >/dev/null 2>/dev/null
./scripts/av-source-eevblog.sh >/dev/null 2>/dev/null &
./scripts/av-source-avsync.sh >/dev/null 2>/dev/null &
pidstat -p $PID 1 &
sleep 10
kill $PID
wait
