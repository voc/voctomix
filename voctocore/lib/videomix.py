import logging
import gi
gi.require_version('GstController', '1.0')

from configparser import NoOptionError
from enum import Enum, unique

from gi.repository import Gst, GstController

from lib.config import Config
from lib.clock import Clock
from lib.transitions import Frame, Composites, Transitions

fps = 50


@unique
class CompositeModes(Enum):
    fullscreen = 0
    side_by_side_equal = 1
    side_by_side_preview = 2
    picture_in_picture = 3


class VideoMix(object):
    log = logging.getLogger('VideoMix')

    class Pad(list):
        """ Pad is the adaptor between the gstreamer compositor
            and voctomix transitions
        """

        def __init__(self, pipeline, sources):
            """ initialize with a gstreamer pipeline and names
                of the sources to manage
            """
            # walk all sources
            for idx in range(len(sources)):
                # get mixer and cropper pad from pipeline
                mixerpad = (pipeline
                            .get_by_name('mix')
                            .get_static_pad('sink_%u' % (idx + 1)))
                cropperpad = (pipeline
                              .get_by_name("video_%u_cropper" % idx))

                def bind(pad, prop):
                    """ adds a binding to a gstreamer property
                        pad's property
                    """
                    # set up control source
                    cs = GstController.InterpolationControlSource()
                    cs.set_property(
                        'mode', GstController.InterpolationMode.NONE)
                    # create control binding
                    cb = GstController.DirectControlBinding.new_absolute(
                        pad, prop, cs)
                    # add binding to pad
                    pad.add_control_binding(cb)
                    # return binding
                    return cs

                # create dictionary of binds to all properties
                # we vary for this source
                self.append({
                    'xpos': bind(mixerpad, 'xpos'),
                    'ypos': bind(mixerpad, 'ypos'),
                    'width': bind(mixerpad, 'width'),
                    'height': bind(mixerpad, 'height'),
                    'alpha': bind(mixerpad, 'alpha'),
                    'zorder': bind(mixerpad, 'zorder'),
                    'croptop': bind(cropperpad, 'top'),
                    'cropleft': bind(cropperpad, 'left'),
                    'cropbottom': bind(cropperpad, 'bottom'),
                    'cropright': bind(cropperpad, 'right')
                })
            # born dirty
            self.dirty = False

        def mix(self, time, frame, source_idx, zorder):
            # get pad for given source
            pad = self[source_idx]
            # transmit frame properties into mixing pipeline
            pad['xpos'].set(time, frame.cropped_left())
            pad['ypos'].set(time, frame.cropped_top())
            pad['width'].set(time, frame.cropped_width())
            pad['height'].set(time, frame.cropped_height())
            pad['alpha'].set(time, frame.float_alpha())
            pad['zorder'].set(time, zorder)
            pad['croptop'].set(time, frame.croptop())
            pad['cropleft'].set(time, frame.cropleft())
            pad['cropbottom'].set(time, frame.cropbottom())
            pad['cropright'].set(time, frame.cropright())

    def __init__(self):
        self.caps = Config.get('mix', 'videocaps')

        self.sources = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        self.log.info("reading composites from configuration...")
        self.composites = Composites.configure(
            Config.items('composites'), self.getInputVideoSize())
        self.targets = Composites.targets(self.composites)
        self.transitions = Transitions.configure(Config.items(
            'transitions'), self.composites, self.targets, fps)
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

        for idx, name in enumerate(self.sources):
            pipeline += """
                intervideosrc channel=video_{name}_mixer !
                {caps} !
                videobox name=video_{idx}_cropper !
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

        self.pad = self.Pad(self.mixingPipeline, self.sources)

        self.log.debug('Initializing Mixer-State')
        self.transition = None
        self.composite = self.composites["fs-a"]
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
        composites = {
            CompositeModes.fullscreen: self.composites["fs-a"],
            CompositeModes.side_by_side_equal: self.composites["sbs"],
            CompositeModes.side_by_side_preview: self.composites["sbsp"],
            CompositeModes.picture_in_picture: self.composites["pip"]
        }
        self.transition = self.transitions.find(
            self.composite, composites[self.compositeMode])
        self.composite = composites[self.compositeMode]
        self.log.info("switching to composite: %s" % self.composite)
        self.pad.dirty = True

    def applyMixerState(self):
        self.log.info('Updating Mixer-State for composite')
        # get play time from mixing pipeline or assume zero
        if self.mixingPipeline.get_clock():
            time = self.mixingPipeline.get_clock().get_time() - \
                self.mixingPipeline.get_base_time()
        else:
            time = 0
        # if a transition is running
        if self.transition:
            # time span for every frame
            span = int(Gst.SECOND / fps)
            # get sources flip point
            flip = self.transition.flip()
            # walk through animation
            for f in range(self.transition.frames()):
                # walk through all sources
                for idx, name in enumerate(self.sources):
                    frame = Frame(alpha=0)

                    # HACK: shitty try to manage zorder
                    zorder = 1
                    if idx == self.sourceA:
                        frame = self.transition.A(f)
                        zorder = 2 if (not flip) or f < flip else 3
                    elif idx == self.sourceB:
                        frame = self.transition.B(f)
                        zorder = 3 if (not flip) or f < flip else 2

                    # apply pad properties
                    self.pad.mix(time, frame, idx, zorder)
                # calculate time for next frame
                time += span
            # transition was applied
            self.transition = None

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
            self.setVideoSourceA(self.sources.index(defSource))
            self.log.info('Changing sourceA to default of Mode %s: %s',
                          compositeModeName, defSource)
        except Exception as e:
            pass

        try:
            defSource = Config.get(sectionName, 'default-b')
            self.setVideoSourceB(self.sources.index(defSource))
            self.log.info('Changing sourceB to default of Mode %s: %s',
                          compositeModeName, defSource)
        except Exception as e:
            pass

    def on_handoff(self, object, buffer):
        if self.pad.dirty:
            self.pad.dirty = False
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
