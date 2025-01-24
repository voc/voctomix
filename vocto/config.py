#!/usr/bin/env python3
import logging
import os
import re
from configparser import ConfigParser

from gi.repository import Gst

from vocto import kind_has_audio, kind_has_video
from vocto.audio_streams import AudioStreams
from vocto.transitions import Composites, Transitions

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

GST_TYPE_AUDIO_TEST_SRC_WAVE = [
    "sine",
    "square",
    "saw",
    "triangle",
    "silence",
    "white-noise",
    "pink-noise",
    "sine-table",
    "ticks",
    "gaussian-noise",
    "red-noise",
    "blue-noise",
    "violet-noise",
]


class VocConfigParser(ConfigParser):
    log = logging.getLogger('VocConfigParser')
    audio_streams = None

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

    def getLiveSources(self):
        return ["mix"] + self.getList('mix', 'livesources', [])

    def getBackgroundSources(self):
        if self.has_option('mix', 'backgrounds'):
            return self.getList('mix', 'backgrounds')
        elif self.has_section('source.background'):
            return ["background"]
        else:
            return []

    def getBackgroundSource(self, composite):
        if not self.getBackgroundSources():
            return None
        for source in self.getBackgroundSources():
            if composite in self.getList('source.{}'.format(source), 'composites', fallback=[]):
                return source
        return self.getBackgroundSources()[0]

    def getSourceKind(self, source):
        return self.get('source.{}'.format(source), 'kind', fallback='test')

    def getNoSignal(self):
        nosignal = self.get('mix', 'nosignal', fallback='smpte100').lower()
        if nosignal in ['none', 'false', 'no']:
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
    
    def getAJADeviceIdentifier(self, source):
        return self.get(f'source.{source}', 'device', fallback='')

    def getAJAInputChannel(self, source):
        return self.getint(f'source.{source}', 'channel', fallback=0)

    def getAJAVideoMode(self, source):
        return self.get(f'source.{source}', 'video_mode', fallback='auto')

    def getAJAAudioSource(self, source):
        return self.get(f'source.{source}', 'audio_source', fallback='embedded')

    def getPulseAudioDevice(self, source):
        return self.get('source.{}'.format(source), 'device', fallback='auto')

    def getAlsaAudioDevice(self, source):
        return self.get('source.{}'.format(source), 'device', fallback='hw:0')

    def getV4l2Device(self, source):
        return self.get('source.{}'.format(source), 'device', fallback='/dev/video0')

    def getV4l2Type(self, source):
        return self.get('source.{}'.format(source), 'type', fallback='video/x-raw')

    def getV4l2Width(self, source):
        return self.get('source.{}'.format(source), 'width', fallback=1920)

    def getV4l2Height(self, source):
        return self.get('source.{}'.format(source), 'height', fallback=1080)

    def getV4l2Format(self, source):
        return self.get('source.{}'.format(source), 'format', fallback='YUY2')

    def getV4l2Framerate(self, source):
        return self.get('source.{}'.format(source), 'framerate', fallback='25/1')

    def getRPICamDevice(self, source):
        return self.get('source.{}'.format(source), 'device', fallback='/dev/video0')

    def getRPICamType(self, source):
        return self.get('source.{}'.format(source), 'type', fallback='video/x-raw')

    def getRPICamWidth(self, source):
        return self.get('source.{}'.format(source), 'width', fallback=1920)

    def getRPICamHeight(self, source):
        return self.get('source.{}'.format(source), 'height', fallback=1080)

    def getRPICamCrop(self, source):
        return self.get('source.{}'.format(source), 'crop', fallback=None)

    def getRPICamFormat(self, source):
        return self.get('source.{}'.format(source), 'format', fallback='YUY2')

    def getRPICamFramerate(self, source):
        return self.get('source.{}'.format(source), 'framerate', fallback='25/1')

    def getRPICamAnnotation(self, source):
        return self.get('source.{}'.format(source), 'annotation', fallback=None)

    def getImageURI(self, source):
        if self.has_option('source.{}'.format(source), 'imguri'):
            return self.get('source.{}'.format(source), 'imguri')
        else:
            path = os.path.abspath(self.get('source.{}'.format(source), 'file'))
            if not os.path.isfile(path):
                self.log.error("image file '%s' could not be found" % path)
            return "file://{}".format(path)

    def getLocation(self, source):
        return self.get('source.{}'.format(source), 'location')

    def getLoop(self, source):
        return self.get('source.{}'.format(source), 'loop', fallback="true")

    def getTestPattern(self, source):
        if not self.has_section('source.{}'.format(source)):
            # default blinder source shall be smpte (if not defined otherwise)
            if source == "blinder":
                return "smpte"
            # default background source shall be black (if not defined otherwise)
            if source in self.getBackgroundSources():
                return "black"

        pattern = self.get('source.{}'.format(source), 'pattern', fallback=None)
        if not pattern:
            global testPatternCount
            testPatternCount += 1
            pattern = GST_TYPE_VIDEO_TEST_SRC_PATTERN[testPatternCount % len(GST_TYPE_VIDEO_TEST_SRC_PATTERN)]
            self.log.info("Test pattern of source '{}' unspecified, picking '{} ({})'"
                          .format(source, pattern, testPatternCount))
        return pattern

    def getTestWave(self, source):
        if not self.has_section('source.{}'.format(source)):
            # background needs no sound, blinder should have no sound
            if source == "blinder" or source == "background":
                return "silence"

        return self.get('source.{}'.format(source), 'wave', fallback="sine")

    def getSourceScan(self, source):
        section = 'source.{}'.format(source)
        if self.has_option(section, 'deinterlace'):
            self.log.error(
                "source attribute 'deinterlace' is obsolete. Use 'scan' instead! Falling back to 'progressive' scheme")
        return self.get(section, 'scan', fallback='progressive')

    def getAudioStreams(self):
        if self.audio_streams is None:
            self.audio_streams = AudioStreams()
            sources = self.getSources()
            for source in sources:
                section = 'source.{}'.format(source)
                if self.has_section(section):
                    self.audio_streams.configure_source(self.items(section), source)
        return self.audio_streams

    def getBlinderAudioStreams(self):
        self.audio_streams = AudioStreams()
        section = 'source.blinder'
        if self.has_section(section):
            self.audio_streams.configure_source(self.items(section), "blinder", use_source_as_name=True)
        return self.audio_streams

    def getAudioStream(self, source):
        '''

        :param source: name of the source in the config file
        :return:
        '''
        section = 'source.{}'.format(source)
        if self.has_section(section):
            return AudioStreams.configure(self.items(section), source)
        return AudioStreams()

    def getNumAudioStreams(self):
        num_audio_streams = len(self.getAudioStreams())
        if self.getAudioChannels() < num_audio_streams:
            self.log.error(
                "number of audio channels in mix/audiocaps differs from the available audio input channels within the sources!")
        return num_audio_streams

    def getAudioChannels(self):
        '''
        get the number of audio channels configured for voc2mix
        :return:
        '''
        caps = Gst.Caps.from_string(self.getAudioCaps()).get_structure(0)
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
        return float(width) / float(height)

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

    def splitOptions(line):
        if len(line) == 0:
            return None
        quote = False
        options = [""]
        for char in line:
            if char == ',' and not quote:
                options.append("")
            else:
                if char == '"':
                    quote = not quote
                options[-1] += char
        return options

    def get_audio_encoder(self, section):
        return self.get(section, 'audioencoder')  # => move to audio_codec class

    def get_sink_audio_channels(self, section):
        return self.getint(section, 'audio_channels')

    def get_sink_audio_map(self, section):
        return self.get(section, 'audio_map')

    def getVideoCodec(self, section):
        if self.has_option(section, 'videocodec'):
            codec = self.get(section, 'videocodec').split(',', 1)
            if len(codec) > 1:
                codec, options = self.get(section, 'videocodec').split(',', 1)
                return codec, VocConfigParser.splitOptions(options) if options else None
            else:
                return codec[0], None
        return "jpeg", ["quality=90"]

    def getVideoEncoder(self, section):
        if self.has_option(section, 'videoencoder'):
            return self.get(section, 'videoencoder')
        return None

    def getVideoDecoder(self, section):
        if self.has_option(section, 'videodecoder'):
            return self.get(section, 'videodecoder')
        return None

    def getDenoise(self, section):
        if self.has_option(section, 'denoise'):
            if self.getboolean(section, 'denoise'):
                return 1
        return 0

    def getScaleMethod(self, section):
        if self.has_option(section, 'scale-method'):
            return self.getint(section, 'scale-method')
        return 0

    def getDeinterlace(self, section):
        return self.getboolean(section, 'deinterlace', fallback=False)

    def getAudioCaps(self, section='mix'):
        if self.has_option(section, 'audiocaps'):
            return self.get(section, 'audiocaps')
        elif self.has_option('mix', 'audiocaps'):
            return self.get('mix', 'audiocaps')
        else:
            return "audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000"

    def getVideoCaps(self, section='mix'):
        if self.has_option(section, 'videocaps'):
            return self.get(section, 'videocaps')
        elif self.has_option('mix', 'videocaps'):
            return self.get('mix', 'videocaps')
        else:
            return "video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1"

    def getPreviewSize(self):
        width = self.getint('previews', 'width') if self.has_option(
            'previews', 'width') else 320
        height = self.getint('previews', 'height') if self.has_option(
            'previews', 'height') else int(width * 9 / 16)
        return (width, height)

    def getLocalRecordingEnabled(self):
        return self.getboolean('localrecording', 'enabled', fallback=False)

    def getSRTServerEnabled(self):
        return self.getboolean('srtserver', 'enabled', fallback=True)

    def getPreviewsEnabled(self):
        return self.getboolean('previews', 'enabled', fallback=False)

    def getAVRawOutputEnabled(self):
        return self.getboolean('avrawoutput', 'enabled', fallback=True)

    def getProgramOutputEnabled(self):
        return self.getboolean('programoutput', 'enabled', fallback=False)

    def getProgramOutputVideoSink(self):
        return self.get('programoutput', 'videosink', fallback="autovideosink")

    def getProgramOutputAudioSink(self):
        return self.get('programoutput', 'audiosink', fallback="autoaudiosink")

    def getLivePreviews(self):
        if self.getBlinderEnabled():
            singleval = self.get('previews', 'live').lower()
            if singleval in ["true", "yes"]:
                return ["mix"]
            if singleval == "all":
                return self.getLiveSources()
            previews = self.getList('previews', 'live')
            result = []
            for preview in previews:
                if preview not in self.getLiveSources():
                    self.log.error(
                        "source '{}' configured in 'preview/live' must be listed in 'mix/livesources'!".format(preview))
                else:
                    result.append(preview)
            return result
        else:
            self.log.warning("configuration attribute 'preview/live' is set but blinder is not in use!")
            return []

    def getComposites(self):
        return Composites.configure(self, self.items('composites'), self.getVideoResolution())

    def getTargetComposites(self):
        return Composites.targets(self, self.getComposites())

    def getTransitions(self, composites):
        return Transitions.configure(self, self.items('transitions'),
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

    def _getInternalSources(self):
        sources = ["mix"]
        if self.getBlinderEnabled():
            sources += ["blinder", "mix-blinded"]
            for source in self.getLiveSources():
                sources += [f"{source}-blinded"]
        return sources

    def getVideoSources(self, internal=False):
        def source_has_video(source):
            return kind_has_video(self.getSourceKind(source))

        sources = self.getSources()
        if internal:
            sources.extend(self._getInternalSources())
        return list(filter(source_has_video, sources))

    def getAudioSources(self, internal=False):
        def source_has_audio(source):
            return kind_has_audio(self.getSourceKind(source))

        sources = self.getSources()
        if internal:
            sources.extend(self._getInternalSources())
        return list(filter(source_has_audio, sources))
