#!/usr/bin/env python3
import logging
from gi.repository import Gst
from configparser import SafeConfigParser
from lib.args import Args
from vocto.transitions import Composites, Transitions

testPatternCount = -1

GST_TYPE_VIDEO_TEST_SRC_PATTERN = [
    "smpte",
    "snow",
    "black"
    "white",
    "red",
    "green",
    "blue",
    "checkers-1",
    "checkers-2",
    "checkers-4",
    "checkers-8",
    "circular",
    "blink",
    "smpte75",
    "zone-plate",
    "gamut",
    "chroma-zone-plate",
    "solid",
    "ball",
    "smpte100",
    "bar"
]


class VocConfigParser(SafeConfigParser):

    log = logging.getLogger('VocConfigParser')

    def getList(self, section, option):
        option = self.get(section, option).strip()
        if len(option) == 0:
            return []

        unfiltered = [x.strip() for x in option.split(',')]
        return list(filter(None, unfiltered))

    def getSources(self):
        return self.getList('mix', 'sources')

    def getAudioSource(self):
        return self.get('mix', 'audiosource', fallback=None)

    def getSlidesSource(self):
        return self.get('mix', 'slides_source_name', fallback=None)

    def getSourceKind(self, source):
        return self.get('source.{}'.format(source), 'kind', fallback='test')

    def getDeckLinkDeviceNumber(self, source):
        return self.get('source.{}'.format(source), 'devicenumber', fallback=0)

    def getDeckLinkAudioConnection(self, source):
        return self.get('source.{}'.format(source), 'audio_connection', fallback='auto')

    def getDeckLinkVideoConnection(self, source):
        return self.get('source.{}'.format(source), 'video_connection', fallback='auto')

    def getDeckLinkVideoMode(self, source):
        return self.get('source.{}'.format(source), 'video_mode', fallback='1080i50')

    def getDeckLinkVideoFormat(self, source):
        return self.get('source.{}'.format(source), 'video_format', fallback='auto')

    def getImageURI(self,source):
        return self.get('source.{}'.format(source), 'imguri')

    def getLocation(self,source):
        return self.get('source.{}'.format(source), 'location')

    def getAudioStreamMap(self, source):
        result = {}
        section = 'source.{}'.format(source)
        if section in Config:
            for key in self[section]:
                m = re.match(r'audiostream\[(\d+)\]', key)
                if m:
                    mapping = self.get(section, key)
                    audiostream = int(m.group(1))
                    n = re.match(r'(\d+)\+(\d+)', mapping)
                    if m:
                        result[audiostream] = (
                            int(n.group(1)), int(n.group(2)),)
                    else:
                        result[audiostream] = (int(mapping), None,)
        return result

    def getTestPattern(self, source):
        pattern = self.get('source.{}'.format(
            source), 'pattern', fallback=None)
        if not pattern:
            global testPatternCount
            testPatternCount += 1
            pattern = testPatternCount
            self.log.info("Pattern unspecified, picking pattern '{} ({})'"
                          .format(GST_TYPE_VIDEO_TEST_SRC_PATTERN[testPatternCount], testPatternCount))
        return pattern

    def getSourceDeinterlace(self, source):
        return self.get('source.{}'.format(source), 'deinterlace', fallback='no')

    def getVolume(self, source):
        return self.getfloat("source.{}".format(source), 'volume', fallback=0.0)

    def setShowVolume(self, show=True):
        self.add_section_if_missing('audio')
        self.set('audio', 'volumecontrol', "true" if show else "false")

    def getVideoCaps(self, section='mix'):
        return self.get(section, 'videocaps')

    def getAudioCaps(self, section='mix'):
        return self.get(section, 'audiocaps')

    def getNumAudioStreams(self):
        return self.getint('mix', 'audiostreams', fallback=1)

    def getVideoSize(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getFramerate(self, section='mix'):
        caps = Gst.Caps.from_string(
            self.getVideoCaps(section)).get_structure(0)
        (_, numerator, denominator) = caps.get_fraction('framerate')
        return (numerator, denominator)

    def getFramesPerSecond(self, section='mix'):
        num, denom = self.getFramerate(section)
        return float(num) / float(denom)

    def getVideoSystem(self):
        return self.get('videodisplay', 'system', fallback='gl')

    def getPlayAudio(self):
        return self.getboolean('audio', 'play', fallback=True)

    def getVolumeControl(self):
        # Check if there is a fixed audio source configured.
        # If so, we will remove the volume sliders entirely
        # instead of setting them up.
        return (self.getboolean('audio', 'volumecontrol', fallback=True)
                or self.getboolean('audio', 'forcevolumecontrol', fallback=False))

    def getStreamBlankerEnabled(self):
        return self.getboolean('stream-blanker', 'enabled', fallback=False)

    def getStreamBlankerSources(self):
        if self.getStreamBlankerEnabled():
            return self.getList('stream-blanker', 'sources')
        else:
            return []

    def getStreamBlankerVolume(self):
        return self.getfloat('stream-blanker', 'volume', fallback=0.0)

    def getMirrorsEnabled(self):
        return self.getboolean('mirrors', 'enabled')

    def getOutputBuffers(self, channel):
        return self.getint('output-buffers', channel, fallback=500)

    def getPreviewVaapi(self):
        if self.has_option('previews', 'vaapi'):
            return self.get('previews', 'vaapi')
        return None

    def getPreviewCaps(self):
        if self.has_option('previews', 'videocaps'):
            return self.getVideoCaps('previews')
        else:
            return self.getVideoCaps()

    def getPreviewSize(self):
        width = self.getint('previews', 'width') if self.has_option(
            'previews', 'width') else 320
        height = self.getint('previews', 'height') if self.has_option(
            'previews', 'height') else int(width * 9 / 16)
        return(width, height)

    def getDeinterlacePreviews(self):
        return self.getboolean('previews', 'deinterlace')

    def getUsePreviews(self):
        # @TODO: why double boolean?
        return self.getPreviewsEnabled() and self.getboolean('previews', 'use')

    def getPreviewsEnabled(self):
        return self.getboolean('previews', 'enabled')

    def getPreviewDecoder(self):
        if self.has_option('previews', 'vaapi'):
            return self.get('previews', 'vaapi')
        else:
            return 'jpeg'

    def getComposites(self):
        return Composites.configure(self.items('composites'), self.getVideoSize())

    def getTargetComposites(self):
        return Composites.targets(self.getComposites())

    def getTransitions(self, composites):
        return Transitions.configure(self.items('transitions'),
                                     composites,
                                     fps=self.getFramesPerSecond())

    def getPreviewNameOverlay(self):
        return self.getboolean('previews', 'nameoverlay',fallback=True)
