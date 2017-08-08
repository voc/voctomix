#!/bin/sh
python3 -m unittest discover -t `dirname $0` -s `dirname $0`/tests/
