#!/bin/sh
pep8 --ignore=E402 .
[ $? = 0 ] && echo "Success!" || echo "There were some warnings."
