#!/usr/bin/env python3
# Test driver for Voctolight plugins.
from lib.config import Config
from lib.plugins.all_plugins import get_plugin

def main():
    plugin = get_plugin(Config)

    try:
        while True:
            print('Tally light on. Press ENTER to turn off, ^C to stop.')
            plugin.tally_on()
            input()
            print('Tally light off. Press ENTER to turn on, ^C to stop.')
            plugin.tally_off()
            input()
    except KeyboardInterrupt:
        pass

if __name__ in '__main__':
    main()
