#!/usr/bin/env python3
import logging

from configparser import NoOptionError
from enum import Enum, unique
from gi.repository import Gst
from lib.config import Config
from lib.clock import Clock
from lib.transitions import Composites, Transitions
from lib.scene import Scene
from lib.args import Args

from vocto.composite_commands import CompositeCommand

class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        # read capabilites and sources from confg file
        self.caps = Config.get('mix', 'videocaps')
        self.sources = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        # load composites from config
        self.log.info("Reading transitions configuration...")
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
            compositor
                name=mix
            ! identity
                name=sig
            ! queue
            ! tee
                name=tee

            interpipesrc
                listen-to=video_background
                format=time
            ! mix.

            tee.
            ! queue
            ! interpipesink
                name=video_mix_out
        """

        if Config.getboolean('previews', 'enabled'):
            pipeline += """
                tee.
                ! queue
                ! interpipesink
                    name=video_mix_preview
            """

        if Config.getboolean('stream-blanker', 'enabled'):
            pipeline += """
                tee.
                ! queue
                ! interpipesink
                    name=video_mix_stream-blanker
            """

        for idx, name in enumerate(self.sources):
            pipeline += """
                interpipesrc
                    listen-to=video_{name}_mixer
                    format=time
                ! videobox
                    name=video_{idx}_cropper
                ! mix.
            """.format(
                name=name,
                idx=idx
            )

        # create pipeline
        self.log.debug('Creating Mixing-Pipeline:\n%s', pipeline)
        self.mixingPipeline = Gst.parse_launch(pipeline)

        if Args.dot:
            self.log.debug('Generating DOT image of videomix pipeline')
            Gst.debug_bin_to_dot_file(
                self.mixingPipeline, Gst.DebugGraphDetails.ALL, "videomix")

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

    def getPlayTime(self):
        # get play time from mixing pipeline or assume zero
        return self.mixingPipeline.get_pipeline_clock().get_time() - \
            self.mixingPipeline.get_base_time()

    def on_handoff(self, object, buffer):
        # sync with self.launch()
        if self.launched:
            if self.scene and self.scene.dirty:
                # push scene to gstreamer
                playTime = self.getPlayTime()
                self.log.debug('Applying new Mixer-State at %d ms', playTime / Gst.MSECOND)
                self.scene.push(playTime)

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.error('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def setCompositeEx(self, newCompositeName=None, newA=None, newB=None, useTransitions = False):
        # expect strings or None as parameters
        assert not newCompositeName or type(newCompositeName) == str
        assert not newA or type(newA) == str
        assert not newB or type(newB) == str

        self.log.info("Request to set new composite to %s(%s,%s)",
                      newCompositeName, newA, newB)

        # get current composite
        if not self.compositeMode:
            curCompositeName = None
            self.log.info("No current composite (initial)")
        else:
            curCompositeName = self.compositeMode
            curA = self.sourceA
            curB = self.sourceB
            self.log.info("Current composite is %s(%s,%s)",
                          curCompositeName, curA, curB)

        # check if there is any None parameter and fill it up with
        # reasonable value from the current scene
        if curCompositeName and not (newCompositeName and newA and newB):
            # use current state if not defined by parameter
            if not newCompositeName:
                newCompositeName = curCompositeName
            if not newA:
                newA = curA if newB != curA else curB
            if not newB:
                newB = curA if newA == curB else curB
            self.log.debug("Completing wildcarded composite to %s(%s,%s)",
                      newCompositeName, newA, newB)
        # post condition: we should have all parameters now
        assert newA != newB
        assert newCompositeName and newA and newB

        # fetch composites
        curComposite = self.composites[curCompositeName] if curCompositeName else None
        newComposite = self.composites[newCompositeName]

        # if new scene is complete
        if newComposite and newA in self.sources and newB in self.sources:
            self.log.info("Setting new composite to %s(%s,%s)",
                          newComposite.name, newA, newB)
            # try to find a matching transition from current to new scene
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
                        self.log.warning("No transition found")
            if transition:
                # apply found transition
                self.log.debug(
                    "committing transition '%s' to scene", transition.name())
                self.scene.commit(targetA, transition.Az(1,2))
                self.scene.commit(targetB, transition.Bz(2,1))
            else:
                # apply new scene (hard cut)
                self.log.debug(
                    "setting composite '%s' to scene", newComposite.name)
                self.scene.set(targetA, newComposite.Az(1))
                self.scene.set(targetB, newComposite.Bz(2))
        else:
            # report unknown elements of the target scene
            if not newComposite:
                self.log.error("Unknown composite '%s'", newCompositeName)
            if not newA in self.sources:
                self.log.error("Unknown source '%s'", newA)
            if not newB in self.sources:
                self.log.error("Unknown source '%s'", newB)

        # remember scene we've set
        self.compositeMode = newComposite.name
        self.sourceA = newA
        self.sourceB = newB

    def setComposite(self, command, useTransitions=False):
        ''' parse switch to the composite described by string command '''
        # expect string as parameter
        assert type(command) == str
        # parse command
        command = CompositeCommand.from_str(command)
        self.log.debug("Setting new composite by string '%s'", command)
        self.setCompositeEx(command.composite, command.A, command.B, useTransitions)

    def getVideoSources(self):
        ''' legacy command '''
        return [self.sourceA, self.sourceB]

    def setVideoSourceA(self, source):
        ''' legacy command '''
        setCompositeEx(None,source,None, useTransitions=False)

    def getVideoSourceA(self):
        ''' legacy command '''
        return self.sourceA

    def setVideoSourceB(self, source):
        ''' legacy command '''
        setCompositeEx(None,None,source, useTransitions=False)

    def getVideoSourceB(self):
        ''' legacy command '''
        return self.sourceB

    def setCompositeMode(self, mode):
        ''' legacy command '''
        setCompositeEx(mode,None,None, useTransitions=False)

    def getCompositeMode(self):
        ''' legacy command '''
        return self.compositeMode

    def getComposite(self):
        ''' legacy command '''
        return str(CompositeCommand(self.compositeMode, self.sourceA, self.sourceB))
