"""
Plugin to provide a tally light interface for a Raspberry Pi's GPIO.

It requires RPi.GPIO.
"""

from .base_plugin import BasePlugin

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except ImportError:
    # We are probably not running on a Raspberry Pi.
    GPIO = None

__all__ = ['RpiGpio']

class RpiGpio(BasePlugin):
    def __init__(self, config):
        if not GPIO:
            raise NotImplementedError('RpiGpio will not work on this platform. Is RPi.GPIO installed?')

        self.gpio_port = int(config.get('rpi', 'gpio'))

        GPIO.setup(self.gpio_port, GPIO.OUT)
        GPIO.output(self.gpio_port, GPIO.HIGH)

    def tally_on(self):
        GPIO.output(self.gpio_port, GPIO.LOW)

    def tally_off(self):
        GPIO.output(self.gpio_port, GPIO.HIGH)
