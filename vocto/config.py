#!/usr/bin/env python3
import logging
import re
import os

from gi.repository import Gst
from configparser import SafeConfigParser
from lib.args import Args
from vocto.transitions import Composites, Transitions

testPatternCount = 0

GST_TYPE_VIDEO_TEST_SRC_PATTERN = [
    "smpte",
    "snow",
    "black",
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
    "solid-color",
    "ball",
    "smpte100",
    "bar",
    "pinwheel",
    "spokes",
    "gradient",
    "colors"
]

DEFAULT_BLINDER_SOURCE = "INTERMISSION"

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
        return self.get('source.{}'.format(source), 'video_mode', fallback='auto')

    def getDeckLinkVideoFormat(self, source):
        return self.get('source.{}'.format(source), 'video_format', fallback='auto')

    def getImageURI(self,source):
        if self.has_option('source.{}'.format(source), 'imguri'):
            return self.get('source.{}'.format(source), 'imguri')
        else:
            path = os.path.abspath(self.get('source.{}'.format(source), 'file'))
            if not os.path.isfile(path):
                self.log.error("image file '%s' could not be found" % path)
            return "file://{}".format(path)

    def getLocation(self,source):
        return self.get('source.{}'.format(source), 'location')

    def getTestPattern(self, source):
        if not self.has_section('source.{}'.format(source)):
            # default blinder source shall be smpte (if not defined otherwise)
            if source == "blinder-" + DEFAULT_BLINDER_SOURCE:
                return "smpte"
            # default background source shall be black (if not defined otherwise)
            if source == "background":
                return "black"

        pattern = self.get('source.{}'.format(source), 'pattern', fallback=None)
        if not pattern:
            global testPatternCount
            testPatternCount += 1
            pattern = GST_TYPE_VIDEO_TEST_SRC_PATTERN[testPatternCount]
            self.log.info("Pattern unspecified, picking pattern '{} ({})'"
                          .format(pattern, testPatternCount))
        return pattern

    def getSourceScan(self, source):
        section = 'source.{}'.format(source)
        if self.has_option(section, 'deinterlace'):
            self.log.error("source attribute 'deinterlace' is obsolete. Use 'scan' instead! Falling back to 'progressive' scheme")
        return self.get(section, 'scan', fallback='progressive')

    def getVolume(self, source):
        return self.getfloat("source.{}".format(source), 'volume', fallback=0.0)

    def setShowVolume(self, show=True):
        self.add_section_if_missing('audio')
        self.set('audio', 'volumecontrol', "true" if show else "false")

    def getVideoCaps(self):
        return self.get('mix', 'videocaps', fallback="video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1")

    def getAudioCaps(self, section='mix'):
        return self.get(section, 'audiocaps', fallback="audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000")

    def getNumAudioStreams(self):
        return self.getint('mix', 'audiostreams', fallback=2)

    def getVideoSize(self):
        caps = Gst.Caps.from_string(
            self.getVideoCaps()).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getVideoRatio(self):
        width, height = self.getVideoSize()
        return float(width)/float(height)

    def getFramerate(self):
        caps = Gst.Caps.from_string(
            self.getVideoCaps()).get_structure(0)
        (_, numerator, denominator) = caps.get_fraction('framerate')
        return (numerator, denominator)

    def getFramesPerSecond(self):
        num, denom = self.getFramerate()
        return float(num) / float(denom)

    def getVideoSystem(self):
        return self.get('videodisplay', 'system', fallback='gl')

    def getPlayAudio(self):
        return self.getboolean('audio', 'play', fallback=False)

    def getVolumeControl(self):
        # Check if there is a fixed audio source configured.
        # If so, we will remove the volume sliders entirely
        # instead of setting them up.
        return (self.getboolean('audio', 'volumecontrol', fallback=True)
                or self.getboolean('audio', 'forcevolumecontrol', fallback=False))

    def getBlinderEnabled(self):
        if self.has_section('stream-blanker'):
            self.log.error("configuration section 'stream-blanker' is obsolete and will be ignored! Use 'blinder' instead!");
        return self.getboolean('blinder', 'enabled', fallback=False)

    def getBlinderSources(self):
        if self.getBlinderEnabled():
            if self.has_section('stream-blanker'):
                self.log.error("configuration section 'stream-blanker' is obsolete and will be ignored! Use 'blinder' instead!");
            if self.has_option('blinder', 'sources'):
                return self.getList('blinder', 'sources')
            else:
                return [DEFAULT_BLINDER_SOURCE]
        else:
            return []

    def getBlinderVolume(self):
        if self.has_section('stream-blanker'):
            self.log.error("configuration section 'stream-blanker' is obsolete and will be ignored! Use 'blinder' instead!");
        return self.getfloat('blinder', 'volume', fallback=0.0)

    def getMirrorsEnabled(self):
        return self.getboolean('mirrors', 'enabled', fallback=False)

    def getMirrorsSources(self):
        if self.getMirrorsEnabled():
            if self.has_option('mirrors', 'sources'):
                return self.getList('mirrors', 'sources')
            else:
                return self.getSources()
        else:
            return []

    def getOutputBuffers(self, channel):
        return self.getint('output-buffers', channel, fallback=500)

    def getPreviewVaapi(self):
        if self.has_option('previews', 'vaapi'):
            return self.get('previews', 'vaapi')
        return None

    def getPreviewCaps(self):
        if self.has_option('previews', 'videocaps'):
            return self.get('previews', 'videocaps', fallback='video/x-raw,width=1024,height=576,framerate=25/1')
        else:
            return self.getVideoCaps()

    def getPreviewSize(self):
        width = self.getint('previews', 'width') if self.has_option(
            'previews', 'width') else 320
        height = self.getint('previews', 'height') if self.has_option(
            'previews', 'height') else int(width * 9 / 16)
        return(width, height)

    def getDeinterlacePreviews(self):
        return self.getboolean('previews', 'deinterlace', fallback=False)

    def getPreviewsEnabled(self):
        return self.getboolean('previews', 'enabled', fallback=False)

    def getLivePreviewEnabled(self):
        if self.getBlinderEnabled():
            return self.getboolean('previews', 'live', fallback=False)
        else:
            self.log.warning("configuration attribute 'preview/live' is set but blinder is not in use!");
            return False

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

    def hasSource(self, source):
        return self.has_section('source.{}'.format(source))

    def hasOverlay(self):
        return self.has_section('overlay')

    def getOverlayAutoOff(self):
        return self.getboolean('overlay', 'auto-off', fallback=True)

    def getOverlayUserAutoOff(self):
        return self.getboolean('overlay', 'user-auto-off', fallback=False)
