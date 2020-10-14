#!/usr/bin/env python3

"""
voctocore application entry point.
"""

import sys
import os
import signal


if __name__ == '__main__':
    # Setup sys path to include the application
    # and required libraries like vocto
    file_path = os.path.dirname(__file__)
    sys.path.insert(0, os.path.abspath(
        os.path.join(file_path, "../")))  # Libraries
    sys.path.insert(0, os.path.abspath(
        os.path.join(file_path, "src/")))  # Application

    # Install signal handler
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Start the voctocore server
    from voctocore import application
    application.start()
