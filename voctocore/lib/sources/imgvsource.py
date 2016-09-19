import logging
from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class ImgVSource(AVSource):

    def __init__(self, name, outputs=None, has_audio=False, has_video=True):
        self.log = logging.getLogger('ImgVSource[{}]'.format(name))
        super().__init__(name, outputs, False, has_video)

        if has_audio:
            self.log.warning("Audio requested from video-only source")

        section = 'source.{}'.format(name)
        self.imguri = Config.get(section, 'imguri')

        self.launch_pipeline()

    def __str__(self):
        return 'ImgVSource[{name}] displaying {uri}'.format(
            name=self.name,
            uri=self.imguri
        )

    def launch_pipeline(self):
        pipeline = """
            uridecodebin uri={uri} !
            videoconvert !
            videoscale !
            imagefreeze name=img
        """.format(
            uri=self.imguri
        )
        self.build_pipeline(pipeline, velem='img')
        self.pipeline.set_state(Gst.State.PLAYING)
