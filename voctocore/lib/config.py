#!/usr/bin/env python3
import os.path
import logging
from configparser import DuplicateSectionError
from lib.args import Args
from vocto.config import VocConfigParser
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone, timedelta
import re

__all__ = ['Config']

Config = None


def scandatetime(str):
    return datetime.scandatetime(str[:19], "%Y-%m-%dT%H:%M:%S")

def scanduration(str):
    r = re.match(r'^(\d+):(\d+)$', str)
    return timedelta(hours=int(r.group(1)), minutes=int(r.group(2)))

class VoctocoreConfigParser(VocConfigParser):

    def __init__(self):
        super().__init__()
        self.events = []
        self.event_current = None
        self.events_update = None
        self.default_person = None

    def add_section_if_missing(self, section):
        try:
            self.add_section(section)
        except DuplicateSectionError:
            pass

    def getOverlayFile(self):
        if self.getSchedule():
            return self.default_person
        elif self.has_option('overlay', 'file'):
            return self.get('overlay', 'file')
        else:
            return None

    def getScheduleRoom(self):
        if self.has_option('overlay', 'schedule-room'):
            return self.get('overlay', 'schedule-room')
        else:
            return None

    def getSchedule(self):
        if self.has_option('overlay', 'schedule-file'):
            if not self.has_option('overlay', 'schedule-room'):
                self.log.error("Using configuration option 'overlay'/'schedule-file' without 'overlay'/'schedule-room' may lead to unexpected overlay selection")
            return self.get('overlay', 'schedule-file')
        else:
            return None

    def _getEvents(self):
        # check if file has been changed before re-read
        if os.path.getmtime(self.getSchedule()) != self.events_update:
            self.events = None
            # parse XML and iterate all schedule/day elements
            self.events = ET.parse(
                self.getSchedule()).getroot().findall('day/room/event')
            self.log.info("read {n} events from file \'{f}\'".format(
                n=len(self.events), f=self.getSchedule()))
            # remember the update time
            self.events_update = os.path.getmtime(self.getSchedule())
        return self.events

    def _getEventNow(self):
        # now = datetime.now()
        now = datetime(2019, 8, 11, 15, 15)
        if (not self.event_current) or now > scandatetime(self.event_current.find('date').text) + scanduration(self.event_current.find('duration').text):
            past = datetime(1999, 1, 1)
            event_now = None
            nowest = past
            for event in self._getEvents():
                if event.find('room').text == self.getScheduleRoom() or not self.getScheduleRoom():
                    time = scandatetime(event.find('date').text)
                    if now >= time and time > nowest:
                        nowest = time
                        self.event_current = event
        return self.event_current

    def getOverlaysTitle(self):
        if self.getSchedule():
            try:
                event = self._getEventNow()
                if event:
                    at = scandatetime(event.find('date').text)
                    return "#{id}   '{title}'    {at} - {until}".format(
                        at=at.strftime("%H:%M"),
                        until=(at + scanduration(event.find('duration').text)).strftime("%H:%M"),
                        id=event.get('id'),
                        title=event.find('title').text)
            except FileNotFoundError:
                self.log.error(
                    'schedule file \'%s\' not found', self.getSchedule())
        return None

    def getOverlayFiles(self):
        ''' generate list of available overlay files by the following opportunities:
            - by 'schedule-file' (and optionally 'schedule-room') from section 'overlay'
            - by 'files' from section 'overlay'
            - by 'file' from section 'overlay'
        '''
        if self.getSchedule():
            try:
                event = self._getEventNow()
                persons = [person.text for person in event.findall(
                    "persons/person")]
                if not persons:
                    self.log.warning('schedule file \'%s\' contains no persons for event #%s',
                                     self.getSchedule(), event.get('id'))
                else:
                    self.log.info('schedule file \'%s\' contains %d person(s) for event #%s: %s', self.getSchedule(
                    ), len(persons), event.get('id'), ",".join([p for p in persons]))
                    self.default_person = persons[0]
                return persons

            except FileNotFoundError:
                self.log.error(
                    'schedule file \'%s\' not found (falling back to configuration options files/file)', self.getSchedule())
        if self.has_option('overlay', 'files'):
            return self.getList('overlay', 'files')
        if self.getOverlayFile():
            return [self.getOverlayFile()]
        self.log.warning(
            'Could not find any availbale overlays in configuration.')
        return []


def load():
    global Config
    files = [
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     '../default-config.ini'),
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     '../config.ini'),
        '/etc/voctomix/voctocore.ini',
        '/etc/voctomix.ini',  # deprecated
        '/etc/voctocore.ini',
        os.path.expanduser('~/.voctomix.ini'),  # deprecated
        os.path.expanduser('~/.voctocore.ini'),
    ]

    if Args.ini_file is not None:
        files.append(Args.ini_file)

    Config = VoctocoreConfigParser()
    readfiles = Config.read(files)

    log = logging.getLogger('ConfigParser')
    log.debug('considered config-files: \n%s',
              "\n".join([
                  "\t\t" + os.path.normpath(file)
                  for file in files
              ]))
    log.debug('successfully parsed config-files: \n%s',
              "\n".join([
                  "\t\t" + os.path.normpath(file)
                  for file in readfiles
              ]))

    if Args.ini_file is not None and Args.ini_file not in readfiles:
        raise RuntimeError('explicitly requested config-file "{}" '
                           'could not be read'.format(Args.ini_file))
