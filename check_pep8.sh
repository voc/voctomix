#!/bin/sh
pep8 .
[ $? = 0 ] && echo "Success!" || echo "There were some warnings."
