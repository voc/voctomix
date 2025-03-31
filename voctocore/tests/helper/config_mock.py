from configparser import NoSectionError, NoOptionError, DuplicateSectionError

from voctocore.lib.config import VoctocoreConfigParser


class ConfigMock(VoctocoreConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sections = {}

    def given(self, section, option, value):
        if section not in self._sections:
            self._sections[section] = {}
        self._sections[section][option] = value
        return self

    def _mock_get(self, section, option, fallback):
        if section not in self._sections:
            if fallback:
                return fallback

            raise NoSectionError(section)

        section_values = self._sections[section]
        if option not in section_values:
            if fallback:
                return fallback

            raise NoOptionError(option, section)

        return section_values[option]

    def add_section(self, section):
        if section in self._sections:
            raise DuplicateSectionError(section)

        self._sections[section] = {}

    def set(self, section, option, value=None):
        if section not in self._sections:
            raise NoSectionError(section)

        self._sections[section][option] = value

    # noinspection PyMethodOverriding
    def get(self, section, option, *, raw=False, vars=None, fallback=None):
        return self._mock_get(section, option, fallback)

    def getint(self, section, option, *, raw=False, vars=None,
               fallback=None, **kwargs):
        return int(self._mock_get(section, option, fallback))

    def getfloat(self, section, option, *, raw=False, vars=None,
                 fallback=None, **kwargs):
        return float(self._mock_get(section, option, fallback))

    def getboolean(self, section, option, *, raw=False, vars=None,
                   fallback=None, **kwargs):
        return self._convert_to_boolean(
            self._mock_get(section, option, fallback))

    def reset(self):
        self._sections = {}
        return self

    def resetToDefaults(self):
        return self \
            .reset() \
            .given("mix", "videocaps",
                   "video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1,interlace-mode=progressive") \
            .given("mix", "audiocaps", "audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000") \
            .given("mix", "sources", "cam1,cam2,slides") \
            .given("mix", "livesources", "slides") \
            .given("programoutput", "enabled", "false") \
            .given("source.cam1", "kind", "test") \
            .given("source.cam1", "width", "1920") \
            .given("source.cam1", "height", "1080") \
            .given("source.cam1", "framerate", "25/1") \
            .given("source.cam1", "audio.cam1", "0+1") \
            .given("source.cam2", "kind", "test") \
            .given("source.cam2", "width", "1920") \
            .given("source.cam2", "height", "1080") \
            .given("source.cam2", "framerate", "25/1") \
            .given("source.slides", "kind", "test") \
            .given("source.slides", "width", "1920") \
            .given("source.slides", "height", "1080") \
            .given("source.slides", "framerate", "25/1") \
            .given("source.slides", "audio.slides", "0+1") \
            .given("source.break", "kind", "file") \
            .given("source.break", "location", "default-pause.ts") \
            .given("source.background", "kind", "img") \
            .given("source.background", "file", "bg1080.png") \
            .given("previews", "enabled", "false") \
            .given("previews", "videocaps", "video/x-h264,width=960,height=540,framerate=25/1") \
            .given("blinder", "enabled", "true") \
            .given("blinder", "videos", "break") \
            .given("source.blinder", "kind", "file") \
            .given("source.blinder", "location", "pause-music-voc.mp3") \
            .given("source.blinder", "audio.blinder", "0+1") \
            .given("mirrors", "enabled", "true") \
            .given("mirrors", "sources", "mix,mix-blinded") \
            .given("composites", "fs.a", "*") \
            .given("composites", "fs.b", "*") \
            .given("composites", "fs.alpha-b", "0") \
            .given("composites", "fs.noswap", "true") \
            .given("composites", "sbs.a", "0.008/0.08 0.49") \
            .given("composites", "sbs.b", "0.503/0.42 0.49") \
            .given("composites", "lec.a", "0.006/0.01 0.75") \
            .given("composites", "lec.b", "0.60/0.42 0.56") \
            .given("composites", "lec.crop-b", "0.31/0") \
            .given("composites", "lec.mirror", "true") \
            .given("transitions", "def", "750, * / *")

    @classmethod
    def WithBasicConfig(cls):
        return ConfigMock().resetToDefaults()
