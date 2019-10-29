import argparse

__all__ = ['Args']

Args = None


def parse():
    global Args

    parser = argparse.ArgumentParser(description='Voctogui')
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

    parser.add_argument('-u', '--ui-file', action='store',
                        help="Load a custom .ui-File")

    parser.add_argument('-H', '--host', action='store',
                        help="Connect to this host "
                             "instead of the configured one.")

    parser.add_argument('-d', '--dot', action='store_true',
                        help="Generate PNG files of DOT graphs of pipelines")

    Args = parser.parse_args()
