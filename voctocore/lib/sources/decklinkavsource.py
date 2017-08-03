import logging
from gi.repository import Gst

from lib.config import Config
from lib.sources.avsource import AVSource


class DeckLinkAVSource(AVSource):

    def __init__(self, name, outputs=None, has_audio=True, has_video=True):
        self.log = logging.getLogger('DecklinkAVSource[{}]'.format(name))
        super().__init__(name, outputs, has_audio, has_video)

        section = 'source.{}'.format(name)
        # Device number, default: 0
        self.device = Config.get(section, 'devicenumber', fallback=0)
        # Audio connection, default: Automatic
        self.aconn = Config.get(section, 'audio_connection', fallback='auto')
        # Video connection, default: Automatic
        self.vconn = Config.get(section, 'video_connection', fallback='auto')
        # Video mode, default: 1080i50
        self.vmode = Config.get(section, 'video_mode', fallback='1080i50')

        self.launch_pipeline()

    def __str__(self):
        return 'DecklinkAVSource[{name}] reading card #{device}'.format(
            name=self.name,
            device=self.device
        )

    def launch_pipeline(self):
        # A video source is required even when we only need audio
        pipeline = """
            decklinkvideosrc
                device-number={device}
                connection={conn}
                mode={mode} !
        """.format(
            device=self.device,
            conn=self.vconn,
            mode=self.vmode
        )

        if self.has_video:
            pipeline += """
                videoconvert !
                yadif !
                videoscale !
                videorate name=deckvideo
            """
        else:
            pipeline += """
                fakesink
            """

        if self.has_audio:
            pipeline += """
                decklinkaudiosrc name=deckaudio
                    device-number={device}
                    connection={conn}
            """.format(
                device=self.device,
                conn=self.aconn
            )

        self.build_pipeline(pipeline, aelem='deckaudio', velem='deckvideo')
        self.pipeline.set_state(Gst.State.PLAYING)

    def restart(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.launch_pipeline()
