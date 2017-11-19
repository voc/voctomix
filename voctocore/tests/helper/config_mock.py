from configparser import NoSectionError, NoOptionError, DuplicateSectionError

from lib.config import VocConfigParser


class ConfigMock(VocConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = {}

    def given(self, section, option, value):
        try:
            self.values[section][option] = value
        except KeyError:
            self.values[section] = {option: value}

        return self

    def _mock_get(self, section, option, fallback):
        if section not in self.values:
            if fallback:
                return fallback

            raise NoSectionError(section)

        section_values = self.values[section]
        if option not in section_values:
            if fallback:
                return fallback

            raise NoOptionError(option, section)

        return section_values[option]

    def add_section(self, section):
        if section in self.values:
            raise DuplicateSectionError(section)

        self.values[section] = {}

    def set(self, section, option, value=None):
        if section not in self.values:
            raise NoSectionError(section)

        self.values[section][option] = value

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
        self.values = {}
        return self

    def resetToDefaults(self):
        return self \
            .reset() \
            .given("mix", "videocaps",
                   "video/x-raw,format=I420,width=1920,height=1080,framerate=25/1") \
            .given("mix", "audiocaps",
                   "audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000") \
            .given("mix", "sources", "cam1,cam2,grabber") \
            .given("mix", "audiostreams", 1) \
            .given("previews", "enabled", "false") \
            .given("previews", "deinterlace", "false") \
            .given("stream-blanker", "enabled", "true") \
            .given("stream-blanker", "sources", "pause,nostream") \
            .given("mirrors", "enabled", "true")

    @classmethod
    def WithBasicConfig(cls):
        return ConfigMock().resetToDefaults()
