import argparse

__all__ = ['Args']

Args = None


def parse():
    global Args

    parser = argparse.ArgumentParser(description='Voctocore')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Also print INFO and DEBUG messages.")

    parser.add_argument('-c', '--color',
                        action='store',
                        choices=['auto', 'always', 'never'],
                        default='auto',
                        help="Control the use of colors in the Log-Output")

    parser.add_argument('-t', '--timestamp', action='store_true',
                        help="Enable timestamps in the Log-Output")

    parser.add_argument('-i', '--ini-file', action='store',
                        help="Load a custom config.ini-File")

    Args = parser.parse_args()
