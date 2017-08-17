#!/bin/sh
set -e

# ignore import-not-at-top (required by gi)
pycodestyle --ignore=E402 .
r=$?

[ $r = 0 ] && echo "Success!" || echo "There were some warnings."
exit $r
