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

        all_gpios = [int(i) for i in config.get('rpi', 'gpios').split(',')]
        self.gpio_port = int(config.get('rpi', 'gpio_red'))

        GPIO.setup(all_gpios, GPIO.OUT)
        GPIO.output(all_gpios, GPIO.HIGH)

    def tally_on(self):
        GPIO.output(self.gpio_port, GPIO.LOW)

    def tally_off(self):
        GPIO.output(self.gpio_port, GPIO.HIGH)
