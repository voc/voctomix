#!/bin/sh


TMP_DIR=$(mktemp -d)
PNG_DIR=$PWD/doc/pipelines

echo Generating temporary DOT files into \'$TMP_DIR\'
export GST_DEBUG_DUMP_DOT_DIR=$TMP_DIR

echo Starting voctocore...
timeout 25s ./voctocore/voctocore.py -v -dg &
echo Waiting 15 seconds...
sleep 15
echo Starting voctogui...
echo Waiting 5 seconds...
timeout 5s ./voctogui/voctogui.py -vv -d

cd $TMP_DIR
echo converting DOT to PNG into \'$PNG_DIR\'...
ls
for j in *.dot; do dot -Tpng -o${PNG_DIR}/${j%}.png ${j}; done
