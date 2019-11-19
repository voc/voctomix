#!/usr/bin/env python3
import os.path
import logging
from configparser import DuplicateSectionError
from lib.args import Args
from vocto.config import VocConfigParser
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
import re
import os

__all__ = ['Config']

Config = None


def scandatetime(str):
    return datetime.strptime(str[:19], "%Y-%m-%dT%H:%M:%S")


def scanduration(str):
    r = re.match(r'^(\d+):(\d+)$', str)
    return timedelta(hours=int(r.group(1)), minutes=int(r.group(2)))


class VoctocoreConfigParser(VocConfigParser):

    def __init__(self):
        super().__init__()
        self.events = []
        self.event_now = None
        self.events_update = None
        self.default_insert = None

    def add_section_if_missing(self, section):
        try:
            self.add_section(section)
        except DuplicateSectionError:
            pass

    def getOverlayFile(self):
        ''' return overlay/file or <None> from INI configuration '''
        if self.has_option('overlay', 'file'):
            return self.getOverlayNameFromFilePath(self.get('overlay', 'file'))
        else:
            return None

    def getScheduleRoom(self):
        ''' return overlay/room or <None> from INI configuration '''
        if self.has_option('overlay', 'room'):
            return self.get('overlay', 'room')
        else:
            return None

    def getScheduleEvent(self):
        ''' return overlay/event or <None> from INI configuration '''
        if self.has_option('overlay', 'event'):
            if self.has_option('overlay', 'room'):
                self.log.warning(
                    "'overlay'/'event' overwrites 'overlay'/'room'")
            return self.get('overlay', 'event')
        else:
            return None

    def getSchedule(self):
        ''' return overlay/schedule or <None> from INI configuration '''
        if self.has_option('overlay', 'schedule'):
            if self.has_option('overlay', 'room') or self.has_option('overlay', 'event'):
                return self.get('overlay', 'schedule')
            else:
                # warn if no room has been defined
                self.log.error(
                    "configuration option 'overlay'/'schedule' ignored when not defining 'room' or 'event' too")
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
        # get currnet date and time
        now = datetime.now()
        # check for option overlay/event
        if self.getScheduleEvent():
            # find event by ID
            for event in self._getEvents():
                if event.get('id') == self.getScheduleEvent():
                    # remember current event
                    self.event_now = event
        else:
            # check if there is no event already running
            if (not self.event_now) or now > scandatetime(self.event_now.find('date').text) + scanduration(self.event_now.find('duration').text):
                # inistialize a past date
                past = datetime(1999, 1, 1)
                # remember nearest start time
                nowest = past
                # iterate events
                for event in self._getEvents():
                    # check for room
                    if event.find('room').text == self.getScheduleRoom() or not self.getScheduleRoom():
                        # get start time
                        time = scandatetime(event.find('date').text)
                        # time nearer then nowest
                        if now >= time and time > nowest:
                            # remember new nearest time
                            nowest = time
                            # rememeber current event
                            self.event_now = event
        return self.event_now

    def getOverlaysPath(self):
        ''' return overlays path or $PWD from INI configuration '''
        if self.has_option('overlay', 'path'):
            return os.path.abspath(self.get('overlay', 'path'))
        else:
            return os.getcwd()

    def getOverlaysTitle(self):
        if self.getSchedule():
            try:
                event = self._getEventNow()
                if event:
                    at = scandatetime(event.find('date').text)
                    return (at.strftime("%Y-%m-%d %H:%M"),
                            (at + scanduration(event.find('duration').text)
                             ).strftime("%Y-%m-%d %H:%M"),
                            event.get('id'),
                            event.find('title').text)
            except FileNotFoundError:
                self.log.error(
                    'schedule file \'%s\' not found', self.getSchedule())
        return None

    def getOverlayFilePath(self, overlay):
        ''' return absolute file path to overlay by given string of overlay
            file name (and maybe |-separated name)
        '''
        # return None if None was given
        if not overlay:
            return None
        # split overlay by "|" if applicable
        filename, name = overlay.split(
            "|") if "|" in overlay else (overlay, None)
        # add PNG default extension if not already within filename
        filename = filename + \
            ".png" if filename and (
                len(filename) < 4 or filename[-4:].lower()) != ".png" else filename
        # return absolute path of filename
        return os.path.join(self.getOverlaysPath(), filename)

    def getOverlayNameFromFilePath(self, filepath):
        ''' return overlay name from filepath (which may have |-separated
            name attached)
        '''
        # return None if None was given
        if not filepath:
            return None
        # split filepath by "|" if applicable
        filepath, name = filepath.split(
            "|") if '|' in filepath else (filepath, None)
        # remove overlay path
        filename = filepath.replace(self.getOverlaysPath() + os.sep, "")
        # remove PNG extension
        filename = filename[:-4] if filename and len(
            filename) > 4 and filename[-4:].lower() == ".png" else filename
        # attach name again if it was given
        return "|".join((filename, name)) if name else filename

    def getOverlayFiles(self):
        ''' generate list of available overlay files by the following opportunities:
            - by 'schedule' (and optionally 'room') from section 'overlay'
            - by 'files' from section 'overlay'
            - by 'file' from section 'overlay'
        '''
        # initialize empty inserts list
        inserts = []

        # checkt for overlay/schedule option
        if self.getSchedule():
            try:

                def generate(event):
                    ''' return all available insert names for event '''
                    # get list of persons from event
                    persons = event.findall("persons/person")
                    # generate insert file names and names
                    inserts = ["event_{eid}_person_{pid}|{text}".format(
                        eid=event.get('id'),
                        pid=person.get('id'),
                        text=person.text) for person in persons]
                    # add a insert for all persons together
                    if len(persons) > 1:
                        inserts += ["event_{eid}_persons|{text}".format(
                            eid=event.get('id'),
                            text=", ".join([person.text for person in persons]))]
                    return inserts

                # get current event
                event = self._getEventNow()
                # generate inserts from event
                inserts = generate(event)
                # if empty show warning
                if not inserts:
                    self.log.warning('schedule file \'%s\' contains no information for inserts of event #%s',
                                     self.getSchedule(),
                                     event.get('id'))
            except FileNotFoundError:
                # show error at file not found
                self.log.error('schedule file \'%s\' not found',
                               self.getSchedule())
        # check for overlay/files option
        if self.has_option('overlay', 'files'):
            # add inserts from files
            inserts += [self.getOverlayNameFromFilePath(o)
                        for o in self.getList('overlay', 'files')]
        # check overlay/file option
        if self.getOverlayFile():
            # append this file if not already in list
            if not self.getOverlayNameFromFilePath(self.getOverlayFile()) in inserts:
                inserts += [self.getOverlayNameFromFilePath(self.getOverlayFile())]
        # make a list of inserts with existing image files
        valid = []
        for i in inserts:
            # get absolute file path
            filename = self.getOverlayFilePath(i.split('|')[0])
            if os.path.isfile(filename):
                # append to valid if existing
                valid.append(i)
            else:
                # report error if not found
                self.log.error(
                    'Could not find overlay image file \'%s\'.' % filename )
        # check if there is any useful result
        if valid:
            self.default_insert = valid[0]
            self.log.info('found %d insert(s): %s',
                          len(valid),
                          ",".join([i for i in valid]))
        else:
            self.default_insert = None
            self.log.warning(
                'Could not find any availbale overlays in configuration.')
        return valid

    def getOverlayBlendTime(self):
        ''' return overlay blending time in milliseconds from INI configuration '''
        if self.has_option('overlay', 'blend'):
            return int(self.get('overlay', 'blend'))
        else:
            return 300





def load():
    global Config

    Config = VoctocoreConfigParser()

    config_file_name = Args.ini_file if Args.ini_file else os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '../default-config.ini')
    readfiles = Config.read([config_file_name])

    log = logging.getLogger('ConfigParser')
    log.debug("successfully parsed config-file: '%s'", config_file_name)

    if Args.ini_file is not None and Args.ini_file not in readfiles:
        raise RuntimeError('explicitly requested config-file "{}" '
                           'could not be read'.format(Args.ini_file))
