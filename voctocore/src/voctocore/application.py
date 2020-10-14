"""
voctocore server application
"""

from voctocore import cli
from voctocore import logging


def start():
    """Start the voctocore server"""
    args = cli.parse_args()

    # Bootstrap application
    logging.configure_from_args(args)

