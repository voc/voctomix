#!/bin/sh
pycodestyle --ignore=E402 .
[ $? = 0 ] && echo "Success!" || echo "There were some warnings."
