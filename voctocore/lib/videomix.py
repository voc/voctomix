#!/usr/bin/env python3
import logging

from configparser import NoOptionError
from enum import Enum, unique
from gi.repository import Gst
from lib.config import Config
from lib.clock import Clock
from lib.transitions import Composites, Transitions
from lib.scene import Scene
from lib.composite_commands import CompositeCommand

useTransitions = True


class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        # read capabilites and sources from confg file
        self.caps = Config.get('mix', 'videocaps')
        self.sources = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        # load composites from config
        self.log.info("reading transitions configuration...")
        self.composites = Composites.configure(
            Config.items('composites'), self.getVideoSize())

        # load transitions from configuration
        self.transitions = Transitions.configure(Config.items(
            'transitions'), self.composites, fps=self.getFramesPerSecond())
        self.scene = None
        self.launched = False

    def launch(self):

        # build GStreamer mixing pipeline descriptor
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

        # create pipeline
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

        self.log.debug('Initializing Mixer-State')
        # initialize pipeline bindings for all sources
        self.scene = Scene(self.sources, self.mixingPipeline, self.transitions.fps)
        self.compositeMode = None
        self.sourceA = None
        self.sourceB = None
        self.setCompositeEx(Composites.targets(self.composites)[0].name, self.sources[0], self.sources[1] )

        bgMixerpad = (self.mixingPipeline.get_by_name('mix')
                      .get_static_pad('sink_0'))
        bgMixerpad.set_property('zorder', 0)

        self.log.debug('Launching Mixing-Pipeline')
        self.mixingPipeline.set_state(Gst.State.PLAYING)
        self.launched = True

    def getVideoSize(self):
        caps = Gst.Caps.from_string(self.caps)
        struct = caps.get_structure(0)
        _, width = struct.get_int('width')
        _, height = struct.get_int('height')

        return width, height

    def getFramesPerSecond(self):
        caps = Gst.Caps.from_string(self.caps)
        struct = caps.get_structure(0)
        _, num, denom = struct.get_fraction('framerate')
        return float(num) / float(denom)

    def playTime(self):
        # get play time from mixing pipeline or assume zero
        return self.mixingPipeline.get_pipeline_clock().get_time() - \
            self.mixingPipeline.get_base_time()

    def on_handoff(self, object, buffer):
        if self.launched:
            if self.scene and self.scene.dirty:
                self.log.debug('[Streaming-Thread]: Pad-State is Dirty, '
                               'applying new Mixer-State at %d ms', self.playTime() / Gst.MSECOND)
                self.scene.push(self.playTime())

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def getVideoSources(self):
        return [self.sourceA, self.sourceB]

    def setVideoSourceA(self, source):
        setCompositeEx(None,source,None)

    def getVideoSourceA(self):
        return self.sourceA

    def setVideoSourceB(self, source):
        setCompositeEx(None,None,source)

    def getVideoSourceB(self):
        return self.sourceB

    def setCompositeMode(self, mode):
        setCompositeEx(mode,None,None)

    def getCompositeMode(self):
        return self.compositeMode

    def getComposite(self):
        return str(CompositeCommand(self.compositeMode, self.sourceA, self.sourceB))

    def setCompositeEx(self, newCompositeName=None, newA=None, newB=None):
        # expect strings or None as parameters
        assert not newCompositeName or type(newCompositeName) == str
        assert not newA or type(newA) == str
        assert not newB or type(newB) == str

        self.log.info("request to set new composite to %s(%s,%s)",
                      newCompositeName, newA, newB)

        # get current composite
        if not self.compositeMode:
            curCompositeName = None
            self.log.info("no current composite (initial)")
        else:
            curCompositeName = self.compositeMode
            curA = self.sourceA
            curB = self.sourceB
            self.log.info("current composite is %s(%s,%s)",
                          curCompositeName, curA, curB)

        # check if there is any None parameter and fill it up with
        # reasonable value from the current scene
        if curCompositeName and not (newCompositeName and newA and newB):
            # use current state if undefined as parameter
            if not newCompositeName:
                newCompositeName = curCompositeName
            if not newA:
                if newB != curA:
                    newA = curA
                else:
                    newA = curB
            if not newB:
                if newA == curB:
                    newB = curA
                else:
                    newB = curB
            self.log.debug("completing new composite to %s(%s,%s)",
                      newCompositeName, newA, newB)
        # post condition: we should have all parameters now
        assert newA != newB
        assert newCompositeName and newA and newB

        # fetch composites
        curComposite = self.composites[curCompositeName] if curCompositeName else None
        newComposite = self.composites[newCompositeName]

        if newComposite and newA in self.sources and newB in self.sources:
            self.log.info("setting new composite to %s(%s,%s)",
                          newComposite.name, newA, newB)
            transition = None
            targetA, targetB = newA, newB
            if useTransitions:
                if curComposite:
                    swap = False
                    if (curA, curB) == (newA, newB):
                        transition, swap = self.transitions.solve(curComposite, newComposite, False)
                    elif (curA, curB) == (newB, newA):
                        transition, swap = self.transitions.solve(curComposite, newComposite, True)
                        if not swap:
                            targetA, targetB = newB, newA
                    if not transition:
                        self.log.warning("no transition found")
            if transition:
                self.log.debug(
                    "committing transition '%s' to scene", transition.name())
                self.scene.commit(targetA, transition.Az(1,2))
                self.scene.commit(targetB, transition.Bz(2,1))
            else:
                self.log.debug(
                    "committing composite '%s' to scene", newComposite.name)
                self.scene.commit(targetA, [newComposite.Az(1)])
                self.scene.commit(targetB, [newComposite.Bz(2)])
        else:
            if not newComposite:
                self.log.error("unknown composite '%s'", newCompositeName)
            if not newA in self.sources:
                self.log.error("unknown source '%s'", newA)
            if not newB in self.sources:
                self.log.error("unknown source '%s'", newB)

        self.log.info("current composite is now %s(%s,%s)",
                      newComposite.name, newA, newB)
        self.compositeMode = newComposite.name
        self.sourceA = newA
        self.sourceB = newB

    def setComposite(self, command):
        ''' parse command and switch to the described composite
        '''
        # expect string as parameter
        assert type(command) == str

        command = CompositeCommand.from_str(command)
        self.log.debug("setting new composite by string '%s'", command)
        self.setCompositeEx(command.composite, command.A, command.B)
