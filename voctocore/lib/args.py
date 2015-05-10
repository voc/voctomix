import argparse

__all__ = ['Args']

parser = argparse.ArgumentParser(description='Voctocore')
parser.add_argument('-v', '--verbose', action='store_true',
	help="Also print INFO and DEBUG messages.")

parser.add_argument('-c', '--color', action='store', choices=['auto', 'always', 'never'], default='auto',
	help="Control the use of colors in the Log-Output")

parser.add_argument('-i', '---config-ini', action='store',
	help="Load a custom config.ini-File")

Args = parser.parse_args()
