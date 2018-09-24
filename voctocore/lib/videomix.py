import logging
from configparser import NoOptionError
from enum import Enum, unique

from gi.repository import Gst, GstController

from lib.config import Config
from lib.clock import Clock
from lib.composites import Frame, Composites

@unique
class CompositeModes(Enum):
    fullscreen = 0
    side_by_side_equal = 1
    side_by_side_preview = 2
    picture_in_picture = 3

class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        self.caps = Config.get('mix', 'videocaps')

        self.names = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.names))

        self.log.info("reading composites from configuration...")
        self.composites = Composites.configure(Config.items('composites'), self.getInputVideoSize())
        self.targets = Composites.targets(self.composites)

        pipeline = """
            compositor name=mix !
            {caps} !
            identity name=sig !
            queue !
            tee name=tee

            intervideosrc channel=video_background !
            {caps} !
            mix.

            tee. ! queue ! intervideosink channel=video_mix_out
        """.format(
            caps=self.caps
        )

        if Config.getboolean('previews', 'enabled'):
            pipeline += """
                tee. ! queue ! intervideosink channel=video_mix_preview
            """

        if Config.getboolean('stream-blanker', 'enabled'):
            pipeline += """
                tee. ! queue ! intervideosink channel=video_mix_stream-blanker
            """

        for idx, name in enumerate(self.names):
            pipeline += """
                intervideosrc channel=video_{name}_mixer !
                {caps} !
                videocrop name=video_{idx}_cropper !
                mix.
            """.format(
                name=name,
                caps=self.caps,
                idx=idx
            )
        self.log.info(pipeline)

        self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
        self.mixingPipeline = Gst.parse_launch(pipeline)
        self.mixingPipeline.use_clock(Clock)

        self.log.debug('Binding Error & End-of-Stream-Signal '
                       'on Mixing-Pipeline')
        self.mixingPipeline.bus.add_signal_watch()
        self.mixingPipeline.bus.connect("message::eos", self.on_eos)
        self.mixingPipeline.bus.connect("message::error", self.on_error)

        self.log.debug('Binding Handoff-Handler for '
                       'Synchronus mixer manipulation')
        sig = self.mixingPipeline.get_by_name('sig')
        sig.connect('handoff', self.on_handoff)

        self.padStateDirty = False

        self.log.debug('Initializing Mixer-State')
        self.compositeMode = CompositeModes.fullscreen
        self.sourceA = 0
        self.sourceB = 1
        self.recalculateMixerState()
        self.applyMixerState()

        bgMixerpad = (self.mixingPipeline.get_by_name('mix')
                      .get_static_pad('sink_0'))
        bgMixerpad.set_property('zorder', 0)

        self.log.debug('Launching Mixing-Pipeline')
        self.mixingPipeline.set_state(Gst.State.PLAYING)

    def getInputVideoSize(self):
        caps = Gst.Caps.from_string(self.caps)
        struct = caps.get_structure(0)
        _, width = struct.get_int('width')
        _, height = struct.get_int('height')

        return width, height

    def recalculateMixerState(self):
        if self.compositeMode == CompositeModes.fullscreen:
            self.composite = self.composites["fs-a"]

        elif self.compositeMode == CompositeModes.side_by_side_equal:
            self.composite = self.composites["sbs"]

        elif self.compositeMode == CompositeModes.side_by_side_preview:
            self.composite = self.composites["sbsp"]

        elif self.compositeMode == CompositeModes.picture_in_picture:
            self.composite = self.composites["pip"]

        self.log.info("switching to composite: %s" % self.composite)

        self.log.debug('Marking Pad-State as Dirty')
        self.padStateDirty = True

    def applyMixerState(self):
        self.log.info('Updating Mixer-State for composite')

        for idx, name in enumerate(self.names):
            # mixerpad 0 = background
            mixerpad = (self.mixingPipeline
                        .get_by_name('mix')
                        .get_static_pad('sink_%u' % (idx + 1)))

            cropper = self.mixingPipeline.get_by_name("video_%u_cropper" % idx)

            frame = Frame(alpha=0)
            zorder = 1
            if idx == self.sourceA:
                frame = self.composite.A()
                zorder = 2
            elif idx == self.sourceB:
                frame = self.composite.B()
                zorder = 3
            if frame:
                self.log.debug('Reconfiguring Mixerpad %u to '
                               'x/y=%u/%u, w/h=%u/%u alpha=%0.2f, zorder=%u',
                               idx, frame.cropped_left(), frame.cropped_top(),
                               frame.cropped_width(), frame.cropped_height(),
                               frame.float_alpha(), zorder)
                mixerpad.set_property('xpos', frame.cropped_left())
                mixerpad.set_property('ypos', frame.cropped_top())
                mixerpad.set_property('width', frame.cropped_width())
                mixerpad.set_property('height', frame.cropped_height())
                mixerpad.set_property('alpha', frame.float_alpha())
                mixerpad.set_property('zorder', zorder)

                self.log.info("Reconfiguring Cropper %d to %d/%d/%d/%d",
                              idx,
                              frame.croptop(),
                              frame.cropleft(),
                              frame.cropbottom(),
                              frame.cropright())
                cropper.set_property("top", frame.croptop())
                cropper.set_property("left", frame.cropleft())
                cropper.set_property("bottom", frame.cropbottom())
                cropper.set_property("right", frame.cropright())

    def selectCompositeModeDefaultSources(self):
        sectionNames = {
            CompositeModes.fullscreen: 'fullscreen',
            CompositeModes.side_by_side_equal: 'side-by-side-equal',
            CompositeModes.side_by_side_preview: 'side-by-side-preview',
            CompositeModes.picture_in_picture: 'picture-in-picture'
        }

        compositeModeName = self.compositeMode.name
        sectionName = sectionNames[self.compositeMode]

        try:
            defSource = Config.get(sectionName, 'default-a')
            self.setVideoSourceA(self.names.index(defSource))
            self.log.info('Changing sourceA to default of Mode %s: %s',
                          compositeModeName, defSource)
        except Exception as e:
            pass

        try:
            defSource = Config.get(sectionName, 'default-b')
            self.setVideoSourceB(self.names.index(defSource))
            self.log.info('Changing sourceB to default of Mode %s: %s',
                          compositeModeName, defSource)
        except Exception as e:
            pass

    def on_handoff(self, object, buffer):
        if self.padStateDirty:
            self.padStateDirty = False
            self.log.debug('[Streaming-Thread]: Pad-State is Dirty, '
                           'applying new Mixer-State')
            self.applyMixerState()

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def setVideoSourceA(self, source):
        # swap if required
        if self.sourceB == source:
            self.sourceB = self.sourceA

        self.sourceA = source
        self.recalculateMixerState()

    def getVideoSourceA(self):
        return self.sourceA

    def setVideoSourceB(self, source):
        # swap if required
        if self.sourceA == source:
            self.sourceA = self.sourceB

        self.sourceB = source
        self.recalculateMixerState()

    def getVideoSourceB(self):
        return self.sourceB

    def setCompositeMode(self, mode, apply_default_source=True):
        self.compositeMode = mode

        if apply_default_source:
            self.selectCompositeModeDefaultSources()

        self.recalculateMixerState()

    def getCompositeMode(self):
        return self.compositeMode
