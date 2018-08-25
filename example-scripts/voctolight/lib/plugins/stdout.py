"""
Plugin to provide a tally light interface via stdout.

This is an example that can be used to build other plugins.
"""

from .base_plugin import BasePlugin

__all__ = ['Stdout']

class Stdout(BasePlugin):
    def tally_on(self):
        print('Tally light on')

    def tally_off(self):
        print('Tally light off')
