import argparse

__all__ = ['Args']

Args = None


def parse():
    global Args

    parser = argparse.ArgumentParser(description='Voctogui')
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help="Set verbosity level by using -v, -vv or -vvv.",
    )

    parser.add_argument(
        '-c',
        '--color',
        action='store',
        choices=['auto', 'always', 'never'],
        default='auto',
        help="Control the use of colors in the Log-Output",
    )

    parser.add_argument(
        '-t',
        '--timestamp',
        action='store_true',
        help="Enable timestamps in the Log-Output",
    )

    parser.add_argument(
        '-i', '--ini-file', action='store', help="Load a custom configuration file"
    )

    parser.add_argument(
        '-H',
        '--host',
        action='store',
        help="Connect to this host " "instead of the configured one.",
    )

    parser.add_argument(
        '-d',
        '--dot',
        action='store_true',
        help="Generate DOT files of pipelines into directory given in environment variable GST_DEBUG_DUMP_DOT_DIR",
    )

    parser.add_argument(
        '-D',
        '--gst-debug-details',
        action='store',
        default=15,
        help="Set details in dot graph. GST_DEBUG_DETAILS must be a combination the following values: 1 = show caps-name on edges, 2 = show caps-details on edges, 4 = show modified parameters on elements, 8 = show element states, 16 = show full element parameter values even if they are very long. Default: 15 = show all the typical details that one might want (15=1+2+4+8)",
    )

    parser.add_argument(
        '-g',
        '--gstreamer-log',
        action='count',
        default=0,
        help="Log gstreamer messages into voctocore log (Set log level by using -g, -gg or -ggg).",
    )

    Args = parser.parse_args()
