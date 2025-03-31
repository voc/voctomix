#!/usr/bin/env python3
import logging
import os
import re
from configparser import ConfigParser

from gi.repository import Gst

from vocto import kind_has_audio, kind_has_video
from vocto.audio_streams import AudioStreams
from vocto.composites import Composite
from vocto.transitions import Composites, Transitions
from typing import Optional

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
    log: logging.Logger
    audio_streams: Optional[AudioStreams] = None

    def __init__(self) -> None:
        super().__init__()
        self.log = logging.getLogger('VocConfigParser')

    def getList(self, section: str, option: str) -> list[str]:
        if self.has_option(section, option):
            option = self.get(section, option).strip()
            if len(option) == 0:
                return []

            unfiltered = [x.strip() for x in option.split(',')]
            return list(filter(None, unfiltered))
        else:
            return []

    def getSources(self) -> list[str]:
        return self.getList('mix', 'sources')

    def getLiveSources(self) -> list[str]:
        return ["mix"] + self.getList('mix', 'livesources')

    def getBackgroundSources(self) -> list[str]:
        if self.has_option('mix', 'backgrounds'):
            return self.getList('mix', 'backgrounds')
        elif self.has_section('source.background'):
            return ["background"]
        else:
            return []

    def getBackgroundSource(self, composite) -> Optional[str]:
        if not self.getBackgroundSources():
            return None
        for source in self.getBackgroundSources():
            if composite in self.getList('source.{}'.format(source), 'composites'):
                return source
        return self.getBackgroundSources()[0]

    def getSourceKind(self, source) -> str:
        return self.get('source.{}'.format(source), 'kind', fallback='test')

    def getNoSignal(self) -> Optional[str]:
        nosignal = self.get('mix', 'nosignal', fallback='smpte100').lower()
        if nosignal in ['none', 'false', 'no']:
            return None
        elif nosignal in GST_TYPE_VIDEO_TEST_SRC_PATTERN:
            return nosignal
        else:
            self.log.error("Configuration value mix/nosignal has unknown pattern '{}'".format(nosignal))
            return None

    def getDeckLinkDeviceNumber(self, source) -> int:
        return self.getint('source.{}'.format(source), 'devicenumber', fallback=0)

    def getDeckLinkAudioConnection(self, source) -> str:
        return self.get('source.{}'.format(source), 'audio_connection', fallback='auto')

    def getDeckLinkVideoConnection(self, source) -> str:
        return self.get('source.{}'.format(source), 'video_connection', fallback='auto')

    def getDeckLinkVideoMode(self, source) -> str:
        return self.get('source.{}'.format(source), 'video_mode', fallback='auto')

    def getDeckLinkVideoFormat(self, source) -> str:
        return self.get('source.{}'.format(source), 'video_format', fallback='auto')
    
    def getAJADeviceIdentifier(self, source) -> str:
        return self.get(f'source.{source}', 'device', fallback='')

    def getAJAInputChannel(self, source) -> int:
        return self.getint(f'source.{source}', 'channel', fallback=0)

    def getAJAVideoMode(self, source) -> str:
        return self.get(f'source.{source}', 'video_mode', fallback='auto')

    def getAJAAudioSource(self, source) -> str:
        return self.get(f'source.{source}', 'audio_source', fallback='embedded')

    def getPulseAudioDevice(self, source) -> str:
        return self.get('source.{}'.format(source), 'device', fallback='auto')

    def getAlsaAudioDevice(self, source) -> str:
        return self.get('source.{}'.format(source), 'device', fallback='hw:0')

    def getV4l2Device(self, source) -> str:
        return self.get('source.{}'.format(source), 'device', fallback='/dev/video0')

    def getV4l2Type(self, source) -> str:
        return self.get('source.{}'.format(source), 'type', fallback='video/x-raw')

    def getV4l2Width(self, source) -> int:
        return self.get('source.{}'.format(source), 'width', fallback=1920)

    def getV4l2Height(self, source) -> int:
        return self.get('source.{}'.format(source), 'height', fallback=1080)

    def getV4l2Format(self, source) -> str:
        return self.get('source.{}'.format(source), 'format', fallback='YUY2')

    def getV4l2Framerate(self, source) -> str:
        return self.get('source.{}'.format(source), 'framerate', fallback='25/1')

    def getRPICamDevice(self, source) -> str:
        return self.get('source.{}'.format(source), 'device', fallback='/dev/video0')

    def getRPICamType(self, source) -> str:
        return self.get('source.{}'.format(source), 'type', fallback='video/x-raw')

    def getRPICamWidth(self, source) -> int:
        return self.get('source.{}'.format(source), 'width', fallback=1920)

    def getRPICamHeight(self, source) -> int:
        return self.get('source.{}'.format(source), 'height', fallback=1080)

    def getRPICamCrop(self, source) -> Optional[str]:
        return self.get('source.{}'.format(source), 'crop', fallback=None)

    def getRPICamFormat(self, source) -> str:
        return self.get('source.{}'.format(source), 'format', fallback='YUY2')

    def getRPICamFramerate(self, source) -> str:
        return self.get('source.{}'.format(source), 'framerate', fallback='25/1')

    def getRPICamAnnotation(self, source) -> Optional[str]:
        return self.get('source.{}'.format(source), 'annotation', fallback=None)

    def getImageURI(self, source) -> str:
        if self.has_option('source.{}'.format(source), 'imguri'):
            return self.get('source.{}'.format(source), 'imguri')
        else:
            path = os.path.abspath(self.get('source.{}'.format(source), 'file'))
            if not os.path.isfile(path):
                self.log.error("image file '%s' could not be found" % path)
            return "file://{}".format(path)

    def getLocation(self, source) -> Optional[str]:
        return self.get('source.{}'.format(source), 'location')

    def getLoop(self, source) -> str:
        return self.get('source.{}'.format(source), 'loop', fallback="true")

    def getTestPattern(self, source) -> str:
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

    def getTestWave(self, source) -> str:
        if not self.has_section('source.{}'.format(source)):
            # background needs no sound, blinder should have no sound
            if source == "blinder" or source == "background":
                return "silence"

        return self.get('source.{}'.format(source), 'wave', fallback="sine")

    def getSourceScan(self, source) -> str:
        section = 'source.{}'.format(source)
        if self.has_option(section, 'deinterlace'):
            self.log.error(
                "source attribute 'deinterlace' is obsolete. Use 'scan' instead! Falling back to 'progressive' scheme")
        return self.get(section, 'scan', fallback='progressive')

    def getAudioStreams(self) -> AudioStreams:
        if self.audio_streams is None:
            self.audio_streams = AudioStreams()
            sources = self.getSources()
            for source in sources:
                section = 'source.{}'.format(source)
                if self.has_section(section):
                    self.audio_streams.configure_source(self.items(section), source)
        return self.audio_streams

    def getBlinderAudioStreams(self) -> AudioStreams:
        self.audio_streams = AudioStreams()
        section = 'source.blinder'
        if self.has_section(section):
            self.audio_streams.configure_source(self.items(section), "blinder", use_source_as_name=True)
        return self.audio_streams

    def getAudioStream(self, source) -> AudioStreams:
        '''

        :param source: name of the source in the config file
        :return:
        '''
        section = 'source.{}'.format(source)
        if self.has_section(section):
            return AudioStreams.configure(self.items(section), source)
        return AudioStreams()

    def getNumAudioStreams(self) -> int:
        num_audio_streams = len(self.getAudioStreams())
        if self.getAudioChannels() < num_audio_streams:
            self.log.error(
                "number of audio channels in mix/audiocaps differs from the available audio input channels within the sources!")
        return num_audio_streams

    def getAudioChannels(self) -> int:
        '''
        get the number of audio channels configured for voc2mix
        :return:
        '''
        caps = self.parseCaps(self.getAudioCaps())
        _, channels = caps.get_int('channels')
        return channels

    def getVideoResolution(self) -> tuple[int, int]:
        caps = self.parseCaps(self.getVideoCaps())
        _, width = caps.get_int('width')
        _, height = caps.get_int('height')
        return (width, height)

    def getVideoRatio(self) -> float:
        width, height = self.getVideoResolution()
        return float(width) / float(height)

    def getFramerate(self) -> tuple[int, int]:
        caps = self.parseCaps(self.getVideoCaps())
        (_, numerator, denominator) = caps.get_fraction('framerate')
        return (numerator, denominator)

    def getFramesPerSecond(self) -> float:
        num, denom = self.getFramerate()
        return float(num) / float(denom)

    def getVideoSystem(self) -> str:
        return self.get('videodisplay', 'system', fallback='gl')

    def getPlayAudio(self) -> bool:
        return self.getboolean('audio', 'play', fallback=False)

    def getVolumeControl(self) -> bool:
        # Check if there is a fixed audio source configured.
        # If so, we will remove the volume sliders entirely
        # instead of setting them up.
        return (self.getboolean('audio', 'volumecontrol', fallback=True)
                or self.getboolean('audio', 'forcevolumecontrol', fallback=False))

    def getBlinderEnabled(self) -> bool:
        return self.getboolean('blinder', 'enabled', fallback=False)

    def isBlinderDefault(self) -> bool:
        return not self.has_option('blinder', 'videos')

    def getBlinderSources(self) -> list[str]:
        if self.getBlinderEnabled():
            if self.isBlinderDefault():
                return ["blinder"]
            else:
                return self.getList('blinder', 'videos')
        else:
            return []

    def getBlinderVolume(self) -> float:
        return self.getfloat('source.blinder', 'volume', fallback=1.0)

    def getMirrorsEnabled(self) -> bool:
        return self.getboolean('mirrors', 'enabled', fallback=False)

    def getMirrorsSources(self) -> list[str]:
        if self.getMirrorsEnabled():
            if self.has_option('mirrors', 'sources'):
                return self.getList('mirrors', 'sources')
            else:
                return self.getSources()
        else:
            return []

    def getOutputBuffers(self, channel) -> int:
        return self.getint('output-buffers', channel, fallback=500)

    @staticmethod
    def splitOptions(line) -> Optional[list[str]]:
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

    @staticmethod
    def parseCaps(caps: str) -> Gst.Structure:
        struct = Gst.Caps.from_string(caps)
        if struct is None:
            raise ValueError("could not parse caps")
        return struct.get_structure(0)

    def get_audio_encoder(self, section: str) -> str:
        return self.get(section, 'audioencoder')  # => move to audio_codec class

    def get_sink_audio_channels(self, section: str) -> int:
        return self.getint(section, 'audio_channels')

    def get_sink_audio_map(self, section: str) -> str:
        return self.get(section, 'audio_map')

    def getVideoCodec(self, section: str) -> tuple[str, Optional[list[str]]]:
        if self.has_option(section, 'videocodec'):
            codec = self.get(section, 'videocodec').split(',', 1)
            if len(codec) > 1:
                codec_name, options = self.get(section, 'videocodec').split(',', 1)
                return codec_name, VocConfigParser.splitOptions(options) if options else None
            else:
                return codec[0], None
        return "jpeg", ["quality=90"]

    def getVideoEncoder(self, section: str) -> Optional[str]:
        if self.has_option(section, 'videoencoder'):
            return self.get(section, 'videoencoder')
        return None

    def getVideoDecoder(self, section: str) -> Optional[str]:
        if self.has_option(section, 'videodecoder'):
            return self.get(section, 'videodecoder')
        return None

    def getDenoise(self, section: str) -> int:
        if self.has_option(section, 'denoise'):
            if self.getboolean(section, 'denoise'):
                return 1
        return 0

    def getScaleMethod(self, section: str) -> int:
        if self.has_option(section, 'scale-method'):
            return self.getint(section, 'scale-method')
        return 0

    def getDeinterlace(self, section: str) -> bool:
        return self.getboolean(section, 'deinterlace', fallback=False)

    def getAudioCaps(self, section='mix') -> str:
        if self.has_option(section, 'audiocaps'):
            return self.get(section, 'audiocaps')
        elif self.has_option('mix', 'audiocaps'):
            return self.get('mix', 'audiocaps')
        else:
            return "audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000"

    def getVideoCaps(self, section='mix') -> str:
        if self.has_option(section, 'videocaps'):
            return self.get(section, 'videocaps')
        elif self.has_option('mix', 'videocaps'):
            return self.get('mix', 'videocaps')
        else:
            return "video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1"

    def getPreviewSize(self) -> tuple[int, int]:
        width = self.getint('previews', 'width') if self.has_option(
            'previews', 'width') else 320
        height = self.getint('previews', 'height') if self.has_option(
            'previews', 'height') else int(width * 9 / 16)
        return (width, height)

    def getLocalRecordingEnabled(self) -> bool:
        return self.getboolean('localrecording', 'enabled', fallback=False)

    def getSRTServerEnabled(self) -> bool:
        return self.getboolean('srtserver', 'enabled', fallback=True)

    def getPreviewsEnabled(self) -> bool:
        return self.getboolean('previews', 'enabled', fallback=False)

    def getAVRawOutputEnabled(self) -> bool:
        return self.getboolean('avrawoutput', 'enabled', fallback=True)

    def getProgramOutputEnabled(self) -> bool:
        return self.getboolean('programoutput', 'enabled', fallback=False)

    def getProgramOutputVideoSink(self) -> str:
        return self.get('programoutput', 'videosink', fallback="autovideosink")

    def getProgramOutputAudioSink(self) -> str:
        return self.get('programoutput', 'audiosink', fallback="autoaudiosink")

    def getLivePreviews(self) -> list[str]:
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

    def getComposites(self) -> dict[str, Composite]:
        return Composites.configure(self.items('composites'), self.getVideoResolution())

    def getTargetComposites(self) -> list[Composite]:
        return Composites.targets(self.getComposites())

    def getTransitions(self, composites: dict[str, Composite]):
        return Transitions.configure(self.items('transitions'), composites, fps=self.getFramesPerSecond())

    def getPreviewNameOverlay(self) -> bool:
        return self.getboolean('previews', 'nameoverlay', fallback=True)

    def hasSource(self, source) -> bool:
        return self.has_section('source.{}'.format(source))

    def hasOverlay(self) -> bool:
        return self.has_section('overlay')

    def getOverlayAutoOff(self) -> bool:
        return self.getboolean('overlay', 'auto-off', fallback=True)

    def getOverlayUserAutoOff(self) -> bool:
        return self.getboolean('overlay', 'user-auto-off', fallback=False)

    def _getInternalSources(self) -> list[str]:
        sources = ["mix"]
        if self.getBlinderEnabled():
            sources += ["blinder", "mix-blinded"]
            for source in self.getLiveSources():
                sources += [f"{source}-blinded"]
        return sources

    def getVideoSources(self, internal=False) -> list[str]:
        def source_has_video(source: str) -> bool:
            return kind_has_video(self.getSourceKind(source))

        sources = self.getSources()
        if internal:
            sources.extend(self._getInternalSources())
        return list(filter(source_has_video, sources))

    def getAudioSources(self, internal=False) -> list[str]:
        def source_has_audio(source: str) -> bool:
            return kind_has_audio(self.getSourceKind(source))

        sources = self.getSources()
        if internal:
            sources.extend(self._getInternalSources())
        return list(filter(source_has_audio, sources))
