#!/usr/bin/env python3
import json
import logging
import os
import os.path
import re
import sys
from configparser import DuplicateSectionError
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from voctocore.lib.args import Args

from vocto.config import VocConfigParser

from typing import Optional, Any, overload

__all__ = ['Config']

Config: 'VoctocoreConfigParser' = None  # type: ignore


def scandatetime(str: str) -> datetime:
    return datetime.strptime(str[:19], "%Y-%m-%dT%H:%M:%S")


def scanduration(str: str) -> Optional[timedelta]:
    r = re.match(r'^(\d+):(\d+)$', str)
    return timedelta(hours=int(r.group(1)), minutes=int(r.group(2)))


class VoctocoreConfigParser(VocConfigParser):
    events: list[dict[str, Any]]
    event_now: Optional[dict[str, Any]]
    event_tz: Optional[Any]
    events_update: Optional[Any]
    default_insert: Optional[Any]

    def __init__(self):
        super().__init__()
        self.events = []
        self.event_now = None
        self.event_tz = None
        self.events_update = None
        self.default_insert = None

    def add_section_if_missing(self, section: str):
        try:
            self.add_section(section)
        except DuplicateSectionError:
            pass

    def getOverlayFile(self) -> Optional[str]:
        ''' return overlay/file or <None> from INI configuration '''
        if self.has_option('overlay', 'file'):
            return self.getOverlayNameFromFilePath(self.get('overlay', 'file'))
        else:
            return None

    def getScheduleRoom(self) -> Optional[str]:
        ''' return overlay/room or <None> from INI configuration '''
        if self.has_option('overlay', 'room'):
            return self.get('overlay', 'room')
        else:
            return None

    def getScheduleEvent(self) -> Optional[str]:
        ''' return overlay/event or <None> from INI configuration '''
        if self.has_option('overlay', 'event'):
            if self.has_option('overlay', 'room'):
                self.log.warning(
                    "'overlay'/'event' overwrites 'overlay'/'room'")
            return self.get('overlay', 'event')
        else:
            return None

    def getSchedule(self) -> Optional[str]:
        ''' return overlay/schedule or <None> from INI configuration '''
        if self.has_option('overlay', 'schedule'):
            if self.has_option('overlay', 'room') or self.has_option('overlay', 'event'):
                return self.get('overlay', 'schedule')
            else:
                # warn if no room has been defined
                self.log.error(
                    "configuration option 'overlay'/'schedule' ignored when not defining 'room' or 'event' too")
        return None

    def _getEvents(self) -> Optional[list[dict[str, Any]]]:
        schedule_path = self.getSchedule()
        if not schedule_path:
            return None

        try:
            # return early if schedule has not been updated since we last
            # read it
            update_time = os.path.getmtime(schedule_path)
            if self.events_update and update_time <= self.events_update:
                return self.events

            # try to load events from json schedule
            with open(schedule_path) as f:
                schedule = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            self.log.error('error while loading schedule from {}: {}'.format(
                schedule_path,
                repr(e),
            ))
            return None
        # try parsing the schedule
        try:
            self.event_tz = ZoneInfo(schedule['schedule']['conference']['time_zone_name'])
            events: list[Any] = []
            for day in schedule['schedule']['conference']['days']:
                for talks_in_room in day['rooms'].values():
                    events.extend(talks_in_room)
            for talk in events:
                if (
                    'date' not in talk
                    or 'duration' not in talk
                    or 'id' not in talk
                    or 'room' not in talk
                    or 'title' not in talk
                ):
                    # the other code assumes these values are there, exit
                    # early if we're missing these.
                    self.logger.error('found malformed talk in {} - missing id/title/date/duration!'.format(
                        schedule_path,
                    ))
                    return None
                # calculate end time for easier calculations later
                start = scandatetime(talk['date'])
                d_h, d_m = talk['duration'].split(':')
                talk['__start_dt'] = start.replace(tzinfo=self.event_tz)
                talk['__end_dt'] = (start + timedelta(hours=int(d_h), minutes=int(d_m))).replace(tzinfo=self.event_tz)
            self.log.info("read {n} events from file '{f}'".format(
                n=len(events),
                f=schedule_path,
            ))
            # remember the update time. do not read it again, to avoid race
            # conditions where the schedule got updated between determining
            # the mtime and the time we finished parsing.
            self.events = events
            self.events_update = update_time
        except Exception as e:
            self.log.error('error while parsing schedule from {}: {}'.format(
                schedule_path,
                repr(e),
            ))
        return self.events

    def _getEventNow(self) -> Optional[dict[str, Any]]:
        # check for option overlay/event
        if self.getScheduleEvent():
            # find event by ID
            for event in self._getEvents():
                if event['id'] == self.getScheduleEvent():
                    # remember current event
                    self.event_now = event
        else:
            NOW = datetime.now(self.event_tz)
            # If no event is currently running, or the current event
            # has already ended, scan the schedule for the next event
            # that happens.
            if (
                not self.event_now
                or NOW >= self.event_now['__end_dt']
            ):
                my_room = self.getScheduleRoom()
                events = self._getEvents()
                if not events:
                    return None

                for event in events:
                    # If we have a room set, but the event is not in
                    # this room, ignore it.
                    if my_room and event['room'] != my_room:
                        continue

                    # This assumes there's no overlapping events
                    if event['__start_dt'] <= NOW < event['__end_dt']:
                        self.event_now = event
                        break
                else:
                    # No event found in self.events
                    self.event_now = None
        return self.event_now

    def getOverlaysPath(self) -> str:
        ''' return overlays path or $PWD from INI configuration '''
        if self.has_option('overlay', 'path'):
            return os.path.abspath(self.get('overlay', 'path'))
        else:
            return os.getcwd()

    def getOverlaysTitle(self) -> Optional[tuple[str, str, Any, Any]]:
        if self.getSchedule():
            event = self._getEventNow()
            if event:
                return (
                    event['__start_dt'].strftime("%Y-%m-%d %H:%M"),
                    event['__end_dt'].strftime("%Y-%m-%d %H:%M"),
                    event['id'],
                    event['title'],
                )
        return None

    @overload
    def getOverlayFilePath(self, overlay: None) -> None: ...
    @overload
    def getOverlayFilePath(self, overlay: str) -> str: ...
    def getOverlayFilePath(self, overlay: Optional[str]) -> Optional[str]:
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

    @overload
    def getOverlayNameFromFilePath(self, filepath: None) -> None: ...
    @overload
    def getOverlayNameFromFilePath(self, filepath: str) -> str: ...
    def getOverlayNameFromFilePath(self, filepath: Optional[str]) -> Optional[str]:
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

    def getOverlayFiles(self) -> list[str]:
        ''' generate list of available overlay files by the following opportunities:
            - by 'schedule' (and optionally 'room') from section 'overlay'
            - by 'files' from section 'overlay'
            - by 'file' from section 'overlay'
        '''
        # initialize empty inserts list
        inserts = []

        # checkt for overlay/schedule option
        if self.getSchedule():
            # get current event
            event = self._getEventNow()
            if event:
                # generate inserts from event
                persons = {}
                # assemble a list of persons which actually have names
                for person in event.get('persons', []):
                    name = person.get('public_name', person.get('name'))
                    if name:
                        persons[name] = person['id']
                if persons:
                    # ensure we always have a 'persons' overlay if we
                    # have persons on schedule
                    inserts.append(
                        "event_{eid}_persons|{text}".format(
                            eid=event['id'],
                            text="{} - {}".format(
                                event.get("title", "no title"),
                                ", ".join(persons),
                            ),
                        )
                    )
                    for pname, pid in sorted(persons.items()):
                        inserts.append(
                            "event_{eid}_person_{pid}|{text}".format(
                                eid=event['id'],
                                pid=pid,
                                text=pname,
                            )
                        )
                # if empty show warning
                if not inserts:
                    self.log.warning('schedule file \'%s\' contains no information for inserts of event #%s',
                                     self.getSchedule(),
                                     event['id'])
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
        valid: list[str] = []
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

    def getOverlayBlendTime(self) -> int:
        ''' return overlay blending time in milliseconds from INI configuration '''
        if self.has_option('overlay', 'blend'):
            return int(self.get('overlay', 'blend'))
        else:
            return 300

    def getAudioMixMatrix(self) -> list[list[float]]:
        if self.has_option('mix', 'audiomixmatrix'):
            # read matrix from config (columns separated by space, rows by slash
            matrix: list[list[float]] = []
            for l, line in enumerate(self.get('mix', 'audiomixmatrix').split('/')):
                matrix.append([])
                for v, value in enumerate(line.split()):
                    matrix[l].append(float(value))
                if len(matrix[0]) != len(matrix[l]):
                    self.log.error('Mix matrix has lines of different lengths')
                    sys.exit(-1)
        else:
            # create identity matrix for all channels
            channels = self.getAudioChannels()
            matrix = [[0.0 for x in range(0, channels)]
                      for x in range(0, channels)]
            for i in range(0, channels):
                matrix[i][i] = 1.0
        return matrix


def load():
    global Config

    Config = VoctocoreConfigParser()

    home_ini_file = os.path.join(Path.home(), '.config/voctomix/voctocore.ini')
    etc_ini_file = '/etc/voctomix/voctocore.ini'
    default_ini_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '../default-config.ini')
    if Args.ini_file:
        config_file_name = Args.ini_file
    elif Path(home_ini_file).is_file():
        config_file_name = home_ini_file
    elif Path(etc_ini_file).is_file():
        config_file_name = etc_ini_file
    else:
        config_file_name = default_ini_file
    readfiles = Config.read([config_file_name])

    log = logging.getLogger('ConfigParser')
    log.debug("successfully parsed config-file: '%s'", config_file_name)

    if Args.ini_file is not None and Args.ini_file not in readfiles:
        raise RuntimeError('explicitly requested config-file "{}" '
                           'could not be read'.format(Args.ini_file))
