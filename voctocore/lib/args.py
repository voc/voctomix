import argparse

__all__ = ['Args']

Args = None


def parse():
    global Args

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

    parser.add_argument('-d', '--dot', action='store_true',
                        help="Generate dot files of pipelines")

    parser.add_argument('-g', '--gstreamer-log', action='count', default=0,
                        help="Log gstreamer messages into voctocore log (Set log level by using -g, -gg or -ggg).")

    Args = parser.parse_args()
