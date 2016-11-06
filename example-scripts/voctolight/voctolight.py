#!/usr/bin/env python3
import sys
import os
import signal
import logging
#import RPi.GPIO as GPIO

# import things reused from voctogui
# todo discuss if a libvocto would be usefull
import lib.connection as Connection

from lib.config import Config
from lib.loghandler import LogHandler
from lib.args import Args

# voctolight class
class Voctolight(object):

    def __init__(self):
        self.log = logging.getLogger('Voctolight')

        self.gpio = Config.get('light', 'gpio')
        self.log.debug(self.gpio)

        self.cam = Config.get('light', 'cam')
        self.log.debug(self.cam)

        self.comp = Connection.fetch_composit_mode()
        self.log.debug(self.comp)

        self.video = Connection.fetch_video()
        self.log.debug(self.video)

        # switch connection to nonblocking, event-driven mode
        Connection.enterNonblockingMode()

    def led_on(self):
        #GPIO.output(self.gpio, GPIO.HIGH)
        self.log.debug('Switching LED on')

    def led_off(self):
        #GPIO.output(self.gpio, GPIO.LOW)
        self.log.debug('Switching LED off')

    def led_status(self):
        self.log.debug('LED status is TBD')

    def led_blink(self):
        self.log.debug('LED will blink')

    def run(self):
        # set initial LED state
        if self.video[0] == self.cam:
            self.led_on()
        elif self.video[1] == self.cam and self.comp != 'fullscreen':
            self.led_on()
        else:
            self.led_off()

        #todo register events


# prepare start of voctolight
def main():
    # configure logging
    docolor = (Args.color == 'always') or (Args.color == 'auto' and
                                           sys.stderr.isatty())

    handler = LogHandler(docolor, Args.timestamp)
    logging.root.addHandler(handler)

    if Args.verbose >= 2:
        level = logging.DEBUG
    elif Args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.root.setLevel(level)

    # make killable by ctrl-c
    logging.debug('setting SIGINT handler')
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logging.info('Python Version: %s', sys.version_info)

    # establish a synchronus connection to server
    Connection.establish(
        Args.host if Args.host else Config.get('server', 'host')
    )

    # fetch config from server
    Config.fetchServerConfig()



    # set LED GPIO
#    GPIO.setmode(GPIO.BOARD)
#    GPIO.setup(11, GPIO.OUT)

    # check if the core uses the same cam name
    if Config.get('light', 'cam') not in Config.get('mix', 'sources'):
        logging.error('Voctocore is not configured for the same cam as voctolight')
        sys.exit(-1)

    # get current composite mode




    voctolight = Voctolight()
    voctolight.run()

if __name__ == '__main__':
    main()