#!/bin/sh
set -e

# ignore import-not-at-top (required by gi)
pycodestyle --ignore=E402 --exclude=voctocore/tests,doc .

# ignore long lines (prefer explanatory test-names)
pycodestyle --ignore=E501 voctocore/tests
