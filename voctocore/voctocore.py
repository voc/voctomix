#!/usr/bin/env python3
import os
import sys

# DEPRECATED
# Use python3 -m voctocore instead of python3 voctocore/voctocore.py

path = os.path.dirname(os.path.abspath(__file__))
sys.path.remove(path)
sys.path.append(os.path.dirname(path))
filename = os.path.join(path, '__main__.py')
with open(filename) as file:
    exec(compile(file.read(), filename, 'exec'))
