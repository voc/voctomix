#!/usr/bin/env python3
import logging
import re
import os

from gi.repository import Gst
from configparser import SafeConfigParser
from lib.args import Args
from vocto.transitions import Composites, Transitions
from vocto.audio_streams import AudioStreams

testPatternCount = 0

GST_TYPE_VIDEO_TEST_SRC_PATTERN = [
    "smpte",
    "ball",
    "red",
    "green",
    "blue",
    "black",
    "white",
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
    "smpte100",
    "bar",
    "snow",
    "pinwheel",
    "spokes",
    "gradient",
    "colors"
]

class VocConfigParser(SafeConfigParser):

    log = logging.getLogger('VocConfigParser')

    def getList(self, section, option, fallback=None):
        if self.has_option(section, option):
            option = self.get(section, option).strip()
            if len(option) == 0:
                return []

            unfiltered = [x.strip() for x in option.split(',')]
            return list(filter(None, unfiltered))
        else:
            return fallback

    def getSources(self):
        return self.getList('mix', 'sources')

    def getAudioSource(self):
        return self.get('mix', 'audiosource', fallback=None)

    def getLiveSources(self):
        return ["mix"] + self.getList('mix', 'livesources', [])

    def getSourceKind(self, source):
        return self.get('source.{}'.format(source), 'kind', fallback='test')

    def getNoSignal(self):
        nosignal = self.get('mix', 'nosignal', fallback='smpte100').lower()
        if nosignal in ['none','false','no']:
            return None
        elif nosignal in GST_TYPE_VIDEO_TEST_SRC_PATTERN:
            return nosignal
        else:
            self.log.error("Configuration value mix/nosignal has unknown pattern '{}'".format(nosignal))

    def getDeckLinkDeviceNumber(self, source):
        return self.getint('source.{}'.format(source), 'devicenumber', fallback=0)

    def getDeckLinkAudioConnection(self, source):
        return self.get('source.{}'.format(source), 'audio_connection', fallback='auto')

    def getDeckLinkVideoConnection(self, source):
        return self.get('source.{}'.format(source), 'video_connection', fallback='auto')

    def getDeckLinkVideoMode(self, source):
        return self.get('source.{}'.format(source), 'video_mode', fallback='auto')

    def getDeckLinkVideoFormat(self, source):
        return self.get('source.{}'.format(source), 'video_format', fallback='auto')

    def getV4l2Device(self, source):
        return self.get('source.{}'.format(source), 'device', fallback='/dev/video0')

    def getV4l2Width(self, source):
        return self.get('source.{}'.format(source), 'width', fallback=1920)

    def getV4l2Height(self, source):
        return self.get('source.{}'.format(source), 'height', fallback=1080)

    def getV4l2Format(self, source):
        return self.get('source.{}'.format(source), 'format', fallback='YUY2')

    def getV4l2Framerate(self, source):
        return self.get('source.{}'.format(source), 'framerate', fallback='25/1')

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
            if source == "blinder":
                return "smpte"
            # default background source shall be black (if not defined otherwise)
            if source == "background":
                return "black"

        pattern = self.get('source.{}'.format(source), 'pattern', fallback=None)
        if not pattern:
            global testPatternCount
            testPatternCount += 1
            pattern = GST_TYPE_VIDEO_TEST_SRC_PATTERN[testPatternCount]
            self.log.info("Test pattern of source '{}' unspecified, picking '{} ({})'"
                          .format(source,pattern, testPatternCount))
        return pattern

    def getSourceScan(self, source):
        section = 'source.{}'.format(source)
        if self.has_option(section, 'deinterlace'):
            self.log.error("source attribute 'deinterlace' is obsolete. Use 'scan' instead! Falling back to 'progressive' scheme")
        return self.get(section, 'scan', fallback='progressive')

    def getAudioStreams(self):
        audio_streams = AudioStreams()
        sources = self.getSources()
        for source in sources:
            section = 'source.{}'.format(source)
            if self.has_section(section):
                audio_streams += AudioStreams.configure(self.items(section), source)
        return audio_streams

    def getBlinderAudioStreams(self):
        audio_streams = AudioStreams()
        section = 'source.blinder'
        if self.has_section(section):
            audio_streams += AudioStreams.configure(self.items(section), "blinder", use_source_as_name=True)
        return audio_streams

    def getAudioStream(self, source):
        section = 'source.{}'.format(source)
        if self.has_section(section):
            return AudioStreams.configure(self.items(section), source)
        return AudioStreams()

    def getNumAudioStreams(self):
        num_audio_streams = len(self.getAudioStreams())
        if self.getAudioChannels() < num_audio_streams:
            self.log.error("number of audio channels in mix/audiocaps differs from the available audio input channels within the sources!")
        return num_audio_streams

    def setShowVolume(self, show=True):
        self.add_section_if_missing('audio')
        self.set('audio', 'volumecontrol', "true" if show else "false")

    def getVideoCaps(self):
        return self.get('mix', 'videocaps', fallback="video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1")

    def getAudioCaps(self, section='mix'):
        return self.get(section, 'audiocaps', fallback="audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000")

    def getAudioChannels(self):
        caps = Gst.Caps.from_string(
            self.getAudioCaps()).get_structure(0)
        _, channels = caps.get_int('channels')
        return channels

    def getVideoResolution(self):
        caps = Gst.Caps.from_string(
            self.getVideoCaps()).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getVideoRatio(self):
        width, height = self.getVideoResolution()
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
        return self.getboolean('blinder', 'enabled', fallback=False)

    def isBlinderDefault(self):
        return not self.has_option('blinder', 'videos')

    def getBlinderSources(self):
        if self.getBlinderEnabled():
            if self.isBlinderDefault():
                return ["blinder"]
            else:
                return self.getList('blinder', 'videos')
        else:
            return []

    def getBlinderVolume(self):
        return self.getfloat('source.blinder', 'volume', fallback=1.0)

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

    def getDenoiseVaapi(self):
        if self.has_option('previews', 'vaapi-denoise'):
            if self.getboolean('previews', 'vaapi-denoise'):
                return 1
        return 0

    def getScaleMethodVaapi(self):
        if self.has_option('previews', 'scale-method'):
            return self.getint('previews', 'scale-method')
        return 0

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

    def getPreviewFramerate(self):
        caps = Gst.Caps.from_string(
            self.getPreviewCaps()).get_structure(0)
        (_, numerator, denominator) = caps.get_fraction('framerate')
        return (numerator, denominator)

    def getPreviewResolution(self):
        caps = Gst.Caps.from_string(
            self.getPreviewCaps()).get_structure(0)
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getDeinterlacePreviews(self):
        return self.getboolean('previews', 'deinterlace', fallback=False)

    def getPreviewsEnabled(self):
        return self.getboolean('previews', 'enabled', fallback=False)

    def getLivePreviews(self):
        if self.getBlinderEnabled():
            singleval = self.get('previews', 'live').lower()
            if singleval in [ "true", "yes" ]:
                return ["mix"]
            if singleval == "all":
                return self.getLiveSources()
            previews = self.getList('previews', 'live')
            result = []
            for preview in previews:
                if preview not in self.getLiveSources():
                    self.log.error("source '{}' configured in 'preview/live' must be listed in 'mix/livesources'!".format(preview));
                else:
                    result.append(preview)
            return result
        else:
            self.log.warning("configuration attribute 'preview/live' is set but blinder is not in use!");
            return []

    def getPreviewDecoder(self):
        if self.has_option('previews', 'vaapi'):
            return self.get('previews', 'vaapi')
        else:
            return 'jpeg'

    def getComposites(self):
        return Composites.configure(self.items('composites'), self.getVideoResolution())

    def getTargetComposites(self):
        return Composites.targets(self.getComposites())

    def getTransitions(self, composites):
        return Transitions.configure(self.items('transitions'),
                                     composites,
                                     fps=self.getFramesPerSecond())

    def getPreviewNameOverlay(self):
        return self.getboolean('previews', 'nameoverlay', fallback=True)

    def hasSource(self, source):
        return self.has_section('source.{}'.format(source))

    def hasOverlay(self):
        return self.has_section('overlay')

    def getOverlayAutoOff(self):
        return self.getboolean('overlay', 'auto-off', fallback=True)

    def getOverlayUserAutoOff(self):
        return self.getboolean('overlay', 'user-auto-off', fallback=False)
