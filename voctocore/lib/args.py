import argparse

__all__ = ['Args']

Args = None


def parse():
    global Args

    print("parse args")
    parser = argparse.ArgumentParser(description='Voctocore')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Set verbosity level by using -v, -vv or -vvv.")

    parser.add_argument('-c', '--color',
                        action='store',
                        choices=['auto', 'always', 'never'],
                        default='auto',
                        help="Control the use of colors in the Log-Output")

    parser.add_argument('-t', '--timestamp', action='store_true',
                        help="Enable timestamps in the Log-Output")

    parser.add_argument('-i', '--ini-file', action='store',
                        help="Load a custom config.ini-File")

    parser.add_argument('-p', '--pipeline', action='store_true',
                        help="Generate text files of pipelines")

    parser.add_argument('-n', '--no-bins', action='store_true',
                        help="Do not use gstreamer bins")

    parser.add_argument('-d', '--dot', action='store_true',
                        help="Generate DOT files of pipelines into directory given in environment variable GST_DEBUG_DUMP_DOT_DIR")

    parser.add_argument('-D', '--gst-debug-details', action='store', default=1,
                        help="Set details in dot graph. GST_DEBUG_DETAILS must be a combination the following values: 1 = show caps-name on edges, 2 = show caps-details on edges, 4 = show modified parameters on elements, 8 = show element states, 16 = show full element parameter values even if they are very long. Default: 15 = show all the typical details that one might want (15=1+2+4+8)")

    parser.add_argument('-g', '--gstreamer-log', action='count', default=0,
                        help="Log gstreamer messages into voctocore log (Set log level by using -g, -gg or -ggg).")

    Args = parser.parse_args()
