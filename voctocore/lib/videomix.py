import logging
from gi.repository import Gst
from configparser import NoOptionError
from enum import Enum, unique

from lib.config import Config
from lib.clock import Clock


@unique
class CompositeModes(Enum):
    fullscreen = 0
    side_by_side_equal = 1
    side_by_side_preview = 2
    picture_in_picture = 3


class PadState(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.alpha = 1.0
        self.xpos = 0
        self.ypos = 0
        self.zorder = 1
        self.width = 0
        self.height = 0


class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        self.caps = Config.get('mix', 'videocaps')

        self.names = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.names))

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
                mix.
            """.format(
                name=name,
                caps=self.caps,
                idx=idx
            )

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
        self.padState = list()
        for idx, name in enumerate(self.names):
            self.padState.append(PadState())

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
            self.recalculateMixerStateFullscreen()

        elif self.compositeMode == CompositeModes.side_by_side_equal:
            self.recalculateMixerStateSideBySideEqual()

        elif self.compositeMode == CompositeModes.side_by_side_preview:
            self.recalculateMixerStateSideBySidePreview()

        elif self.compositeMode == CompositeModes.picture_in_picture:
            self.recalculateMixerStatePictureInPicture()

        self.log.debug('Marking Pad-State as Dirty')
        self.padStateDirty = True

    def recalculateMixerStateFullscreen(self):
        self.log.info('Updating Mixer-State for Fullscreen-Composition')

        for idx, name in enumerate(self.names):
            pad = self.padState[idx]

            pad.reset()
            pad.alpha = float(idx == self.sourceA)

    def recalculateMixerStateSideBySideEqual(self):
        self.log.info('Updating Mixer-State for '
                      'Side-by-side-Equal-Composition')

        width, height = self.getInputVideoSize()
        self.log.debug('Video-Size parsed as %ux%u', width, height)

        try:
            gutter = Config.getint('side-by-side-equal', 'gutter')
            self.log.debug('Gutter configured to %u', gutter)
        except NoOptionError:
            gutter = int(width / 100)
            self.log.debug('Gutter calculated to %u', gutter)

        targetWidth = int((width - gutter) / 2)
        targetHeight = int(targetWidth / width * height)

        self.log.debug('Video-Size calculated to %ux%u',
                       targetWidth, targetHeight)

        xa = 0
        xb = width - targetWidth
        y = int((height - targetHeight) / 2)

        try:
            ya = Config.getint('side-by-side-equal', 'atop')
            self.log.debug('A-Video Y-Pos configured to %u', ya)
        except NoOptionError:
            ya = y
            self.log.debug('A-Video Y-Pos calculated to %u', ya)

        try:
            yb = Config.getint('side-by-side-equal', 'btop')
            self.log.debug('B-Video Y-Pos configured to %u', yb)
        except NoOptionError:
            yb = y
            self.log.debug('B-Video Y-Pos calculated to %u', yb)

        for idx, name in enumerate(self.names):
            pad = self.padState[idx]
            pad.reset()

            pad.width = targetWidth
            pad.height = targetHeight

            if idx == self.sourceA:
                pad.xpos = xa
                pad.ypos = ya
                pad.zorder = 1

            elif idx == self.sourceB:
                pad.xpos = xb
                pad.ypos = yb
                pad.zorder = 2

            else:
                pad.alpha = 0

    def recalculateMixerStateSideBySidePreview(self):
        self.log.info('Updating Mixer-State for '
                      'Side-by-side-Preview-Composition')

        width, height = self.getInputVideoSize()
        self.log.debug('Video-Size parsed as %ux%u', width, height)

        try:
            asize = [int(i) for i in Config.get('side-by-side-preview',
                                                'asize').split('x', 1)]
            self.log.debug('A-Video-Size configured to %ux%u',
                           asize[0], asize[1])
        except NoOptionError:
            asize = [
                int(width / 1.25),  # 80%
                int(height / 1.25)  # 80%
            ]
            self.log.debug('A-Video-Size calculated to %ux%u',
                           asize[0], asize[1])

        try:
            apos = [int(i) for i in Config.get('side-by-side-preview',
                                               'apos').split('/', 1)]
            self.log.debug('A-Video-Position configured to %u/%u',
                           apos[0], apos[1])
        except NoOptionError:
            apos = [
                int(width / 100),  # 1%
                int(width / 100)  # 1%
            ]
            self.log.debug('A-Video-Position calculated to %u/%u',
                           apos[0], apos[1])

        try:
            bsize = [int(i) for i in Config.get('side-by-side-preview',
                                                'bsize').split('x', 1)]
            self.log.debug('B-Video-Size configured to %ux%u',
                           bsize[0], bsize[1])
        except NoOptionError:
            bsize = [
                int(width / 4),  # 25%
                int(height / 4)  # 25%
            ]
            self.log.debug('B-Video-Size calculated to %ux%u',
                           bsize[0], bsize[1])

        try:
            bpos = [int(i) for i in Config.get('side-by-side-preview',
                                               'bpos').split('/', 1)]
            self.log.debug('B-Video-Position configured to %u/%u',
                           bpos[0], bpos[1])
        except NoOptionError:
            bpos = [
                width - int(width / 100) - bsize[0],
                height - int(width / 100) - bsize[1]  # 1%
            ]
            self.log.debug('B-Video-Position calculated to %u/%u',
                           bpos[0], bpos[1])

        for idx, name in enumerate(self.names):
            pad = self.padState[idx]
            pad.reset()

            if idx == self.sourceA:
                pad.xpos, pad.ypos = apos
                pad.width, pad.height = asize
                pad.zorder = 1

            elif idx == self.sourceB:
                pad.xpos, pad.ypos = bpos
                pad.width, pad.height = bsize
                pad.zorder = 2

            else:
                pad.alpha = 0

    def recalculateMixerStatePictureInPicture(self):
        self.log.info('Updating Mixer-State for '
                      'Picture-in-Picture-Composition')

        width, height = self.getInputVideoSize()
        self.log.debug('Video-Size parsed as %ux%u', width, height)

        try:
            pipsize = [int(i) for i in Config.get('picture-in-picture',
                                                  'pipsize').split('x', 1)]
            self.log.debug('PIP-Size configured to %ux%u',
                           pipsize[0], pipsize[1])
        except NoOptionError:
            pipsize = [
                int(width / 4),  # 25%
                int(height / 4)  # 25%
            ]
            self.log.debug('PIP-Size calculated to %ux%u',
                           pipsize[0], pipsize[1])

        try:
            pippos = [int(i) for i in Config.get('picture-in-picture',
                                                 'pippos').split('/', 1)]
            self.log.debug('PIP-Position configured to %u/%u',
                           pippos[0], pippos[1])
        except NoOptionError:
            pippos = [
                width - pipsize[0] - int(width / 100),  # 1%
                height - pipsize[1] - int(width / 100)  # 1%
            ]
            self.log.debug('PIP-Position calculated to %u/%u',
                           pippos[0], pippos[1])

        for idx, name in enumerate(self.names):
            pad = self.padState[idx]
            pad.reset()

            if idx == self.sourceA:
                pass
            elif idx == self.sourceB:
                pad.xpos, pad.ypos = pippos
                pad.width, pad.height = pipsize
                pad.zorder = 2

            else:
                pad.alpha = 0

    def applyMixerState(self):
        for idx, state in enumerate(self.padState):
            # mixerpad 0 = background
            mixerpad = (self.mixingPipeline
                            .get_by_name('mix')
                            .get_static_pad('sink_%u' % (idx + 1)))

            self.log.debug('Reconfiguring Mixerpad %u to '
                           'x/y=%u/%u, w/h=%u/%u alpha=%0.2f, zorder=%u',
                           idx, state.xpos, state.ypos,
                           state.width, state.height,
                           state.alpha, state.zorder)
            mixerpad.set_property('xpos', state.xpos)
            mixerpad.set_property('ypos', state.ypos)
            mixerpad.set_property('width', state.width)
            mixerpad.set_property('height', state.height)
            mixerpad.set_property('alpha', state.alpha)
            mixerpad.set_property('zorder', state.zorder)

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

    def setCompositeMode(self, mode):
        self.compositeMode = mode

        self.selectCompositeModeDefaultSources()
        self.recalculateMixerState()

    def getCompositeMode(self):
        return self.compositeMode
