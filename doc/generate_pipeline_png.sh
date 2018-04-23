#!/bin/sh


TMP_DIR=$(mktemp -d)
PNG_DIR=$PWD/doc/pipelines

echo Generating temporary DOT files into \'$TMP_DIR\'
export GST_DEBUG_DUMP_DOT_DIR=$TMP_DIR

echo Starting voctocore...
timeout 10s ./voctocore/voctocore.py &
echo Waiting 5 seconds...
sleep 5
echo Starting voctogui...
echo Waiting 5 seconds...
timeout 5s ./voctogui/voctogui.py

cd $TMP_DIR
echo converting DOT to PNG into \'$PNG_DIR\'...
for j in *.dot; do dot "$j" > "${PNG_DIR}/${j%}.png"; done
