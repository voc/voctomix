#!/bin/sh
d=$(dirname $0)
$d/fake-gi.sh
python3 -m unittest discover -t `dirname $0` -s `dirname $0`/tests/
$d/remove-fake-gi.sh
