import logging
import re

from configparser import NoOptionError
from enum import Enum, unique
from gi.repository import Gst
from lib.config import Config
from lib.clock import Clock
from lib.transitions import Composites, Transitions
from lib.scene import Scene

useTransitions = True

class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        # read capabilites and sources from confg file
        self.caps = Config.get('mix', 'videocaps')
        self.sources = Config.getlist('mix', 'sources')
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        # get fps from video capabilities
        r = re.match(
            r'^.*framerate=(\d+)/(\d+).*$', self.caps)
        assert r
        fps = float(r.group(1)) / float(r.group(2))

        # load composites from config
        self.log.info("reading transitions configuration...")
        self.composites = Composites.configure(
            Config.items('composites'), self.getInputVideoSize())

        # load transitions from configuration
        self.transitions = Transitions.configure(Config.items(
            'transitions'), self.composites, fps=fps)

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
        self.scene = Scene(self.sources, self.mixingPipeline, fps)
        self.composite = None
        self.sourceA = None
        self.sourceB = None
        self.setComposite("fs-a(cam1,cam2)")

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

    def playTime(self):
        # get play time from mixing pipeline or assume zero
        return self.mixingPipeline.get_pipeline_clock().get_time() - \
            self.mixingPipeline.get_base_time()

    def on_handoff(self, object, buffer):
        if self.scene.dirty:
            self.log.debug('[Streaming-Thread]: Pad-State is Dirty, '
                           'applying new Mixer-State')
            self.scene.push(self.playTime())

    def on_eos(self, bus, message):
        self.log.debug('Received End-of-Stream-Signal on Mixing-Pipeline')

    def on_error(self, bus, message):
        self.log.debug('Received Error-Signal on Mixing-Pipeline')
        (error, debug) = message.parse_error()
        self.log.debug('Error-Details: #%u: %s', error.code, debug)

    def getVideoSourceA(self):
        return self.sourceA

    def getVideoSourceB(self):
        return self.sourceB

    def getComposite(self):
        return self.composite

    def setCompositeEx(self, newComposite=None, newA=None, newB=None):
        # expect strings or None as parameters
        assert not newComposite or type(newComposite) == str
        assert not newA or type(newA) == str
        assert not newB or type(newB) == str

        self.log.info("request to set new composite to %s(%s,%s)",
                      newComposite, newA, newB)

        curComposite = None
        # check if there is a current composite
        if self.composite:
            curComposite = self.composite
            curA = self.sourceA
            curB = self.sourceB
            self.log.info("current composite is %s(%s,%s)",
                          curComposite, curA, curB)
            #if self.composites[curComposite].covered() and newB:
            #    curB = newB

            # use current state if undefined as parameter
            if not newComposite:
                newComposite = self.composite
            if not newA:
                newA = curA
            if not newB:
                if newA == curB:
                    newB = curA
                else:
                    newB = curB
        else:
            self.log.info("no current composite (initial)")
        assert newA != newB
        assert newA and newB

        self.log.info("setting new composite to %s(%s,%s)",
                      newComposite, newA, newB)
        if (newComposite in self.composites.keys()) and newA and newB:
            if newComposite[0] == '^':
                c = c.swapped()
                newComposite = newComposite[1:]
            c = self.composites[newComposite]
            transition = None
            if useTransitions:
                if curComposite:
                    if (curA,curB) == (newA,newB):
                        x = self.composites[curComposite]
                    elif (curA,curB) == (newB,newA):
                        x = self.composites[curComposite]
                        if x.covered():
                            c = c.swapped()
                            newA, newB = newB, newA
                            self.log.info("swapping new composite from %s to %s", newComposite, c.name)
                            newComposite = "^" + newComposite
                        else:
                            x = x.swapped()
                            self.log.info("swapping current composite from %s to %s", curComposite, x.name)
                            curComposite = x.name
                    transition = self.transitions.find(x, c)
                if not transition:
                    self.log.warning("no transition found")
            if transition:
                self.log.debug(
                    "committing transition '%s' to scene", transition.name())
                self.scene.commit(newA, transition.Az(1,2))
                self.scene.commit(newB, transition.Bz(2,1))
            else:
                self.log.debug(
                    "committing composite '%s' to scene", newComposite)
                self.scene.commit(newA, [c.Az(1)])
                self.scene.commit(newB, [c.Bz(2)])
            self.log.info("current composite is now %s(%s,%s)",
                          newComposite, newA, newB)
            self.composite = newComposite
            self.sourceA = newA
            self.sourceB = newB
        else:
            self.log.warning("composite '%s' not found in configuration", newComposite)

    def setComposite(self, command):
        ''' parse command and switch to the described composite
        '''
        # expect string as parameter
        assert type(command) == str

        self.log.debug("setting new composite by string '%s'", command)
        A = None
        B = None
        # match case: c(A,B)
        r = re.match(
            r'^\s*([-_\w*]+)\s*\(\s*([-_\w*]+)\s*,\s*([-_\w*]+)\)\s*$', command)
        if r:
            A = r.group(2)
            B = r.group(3)
        else:
            # match case: c(A)
            r = re.match(r'^\s*([-_\w*]+)\s*\(\s*([-_\w*]+)\s*\)\s*$', command)
            if r:
                A = r.group(2)
            else:
                # match case: c
                r = re.match(r'^\s*([-_\w*]+)\s*$', command)
                assert r
        composite = r.group(1)
        if composite == '*':
            composite = None
        if A == '*':
            A = None
        if B == '*':
            B = None
        self.setCompositeEx(composite, A, B)
