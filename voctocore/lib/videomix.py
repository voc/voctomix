#!/usr/bin/env python3
import logging

from configparser import NoOptionError
from enum import Enum, unique
from gi.repository import Gst
from lib.config import Config
from vocto.transitions import Composites, Transitions, Frame
from lib.scene import Scene

from vocto.composite_commands import CompositeCommand

class VideoMix(object):
    log = logging.getLogger('VideoMix')

    def __init__(self):
        # read sources from confg file
        self.sources = Config.getSources()
        self.log.info('Configuring Mixer for %u Sources', len(self.sources))

        # load composites from config
        self.log.info("Reading transitions configuration...")
        self.composites = Config.getComposites()

        # load transitions from configuration
        self.transitions = Config.getTransitions(self.composites)
        self.scene = None

        # build GStreamer mixing pipeline descriptor
        self.bin = """
bin.(
    name=VideoMix

    compositor
        name=videomixer
    """
        if Config.hasOverlay():
            self.bin += """\
    ! queue
        name=queue-overlay
    ! gdkpixbufoverlay
        name=overlay
        overlay-width={width}
        overlay-height={height}
""".format(width=Config.getVideoSize()[0],height=Config.getVideoSize()[1])
            if Config.getOverlayFile():
                self.bin += """\
        location={overlay}
""".format(overlay=Config.getOverlayFile())
            else:
                self.log.info("No initial overlay source configured.")

        self.bin += """\
    ! identity
        name=sig
    ! {vcaps}
    ! tee
        name=video-mix

    video-background.
    ! queue
        name=queue-video-background
    ! videomixer.
""".format(
        vcaps=Config.getVideoCaps()
    )

        for idx, name in enumerate(self.sources):
            self.bin += """
    video-{name}.
    ! queue
        name=queue-cropper-{name}
    ! videobox
        name=cropper-{name}
    ! videomixer.
""".format(
                name=name,
                idx=idx
            )

        self.bin += """)
"""

    def attach( self, pipeline ):
        self.log.debug('Binding Handoff-Handler for '
                       'Synchronus mixer manipulation')
        self.pipeline = pipeline
        sig = pipeline.get_by_name('sig')
        sig.connect('handoff', self.on_handoff)

        # get overlay element
        self.overlay = pipeline.get_by_name('overlay')
        # set overlay of by default
        self.showOverlay(Config.getOverlayFile() != None)

        self.log.debug('Initializing Mixer-State')
        # initialize pipeline bindings for all sources
        self.scene = Scene(self.sources, pipeline, self.transitions.fps, 1)
        self.compositeMode = None
        self.sourceA = None
        self.sourceB = None
        self.setCompositeEx(Composites.targets(self.composites)[0].name, self.sources[0], self.sources[1] )

        bgMixerpad = (pipeline.get_by_name('videomixer')
                      .get_static_pad('sink_0'))
        bgMixerpad.set_property('zorder', 0)

    def __str__(self):
        return 'VideoMix'

    def getPlayTime(self):
        # get play time from mixing pipeline or assume zero
        return self.pipeline.get_pipeline_clock().get_time() - \
            self.pipeline.get_base_time()

    def on_handoff(self, object, buffer):
        # sync with self.launch()
        if self.scene and self.scene.dirty:
            # push scene to gstreamer
            playTime = self.getPlayTime()
            self.log.debug('Applying new Mixer-State at %d ms', playTime / Gst.MSECOND)
            self.scene.push(playTime)

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
            # make all other sources invisible
            for source in self.sources:
                if source not in [targetA, targetB]:
                    self.log.debug("making source %s invisible", source)
                    self.scene.set(source, Frame(True,alpha=0,zorder=-1))
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

    def setOverlay(self, location):
        ''' set up overlay file by location '''
        self.overlay.set_property('location', location if location else "" )

    def showOverlay(self, visible):
        ''' set overlay visibility '''
        self.overlay.set_property('alpha', 1.0 if visible else 0.0 )

    def getOverlay(self):
        ''' get current overlay file location '''
        return self.overlay.get_property('location' )

    def getOverlayVisible(self):
        ''' get overlay visibility '''
        return self.overlay.get_property('alpha') != 0.0
