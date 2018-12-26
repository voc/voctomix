#!/usr/bin/env python3
import logging
import gi
gi.require_version('GstController', '1.0')
from gi.repository import Gst, GstController
from lib.transitions import Frame, L, T, R, B

class Scene:
    """ Scene is the adaptor between the gstreamer compositor
        and voctomix frames.
        With commit() you add frames at a specified play time
    """
    log = logging.getLogger('Scene')

    def __init__(self, sources, pipeline, fps):
        """ initialize with a gstreamer pipeline and names
            of the sources to manage
        """
        # frames to apply from
        self.frames = dict()
        # binding pads to apply to
        self.pads = dict()
        # time per frame
        self.frame_time = int(Gst.SECOND / fps)

        def bind(pad, prop):
            """ adds a binding to a gstreamer property
                pad's property
            """
            # set up a new control source
            cs = GstController.InterpolationControlSource()
            # stop control source's internal interpolation
            cs.set_property(
                'mode', GstController.InterpolationMode.NONE)
            # create control binding
            cb = GstController.DirectControlBinding.new_absolute(
                pad, prop, cs)
            # add binding to pad
            pad.add_control_binding(cb)
            # return binding
            return cs

        # walk all sources
        for idx, source in enumerate(sources):
            # initially invisible
            self.frames[source] = None
            # get mixer and cropper pad from pipeline
            mixerpad = (pipeline
                        .get_by_name('videomixer')
                        .get_static_pad('sink_%s' % (idx + 1)))
            cropperpad = (pipeline
                          .get_by_name("cropper-%s" % source))
            # add dictionary of binds to all properties
            # we vary for this source
            self.pads[source] = {
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
            }
        # ready to initialize gstreamer
        self.dirty = False

    def commit(self, source, frames):
        ''' commit multiple frames to the current gstreamer scene '''
        self.log.debug("Commit %d frame(s) to source %s", len(frames), source)
        self.frames[source] = frames
        self.dirty = True

    def set(self, source, frame):
        ''' commit single frame to the current gstreamer scene '''
        self.log.debug("Set frame to source %s", source)
        self.frames[source] = [frame]
        self.dirty = True

    def push(self, at_time=0):
        ''' apply all committed frames to GStreamer pipeline '''
        # get pad for given source
        for source, frames in self.frames.items():
            if not frames:
                frames = [Frame(zorder=-1,alpha=0)]
            self.log.info("Pushing %d frame(s) to source '%s' at time %dms", len(
                frames), source, at_time / Gst.MSECOND)
            # reset time
            time = at_time
            # get GStreamer property pad for this source
            pad = self.pads[source]
            self.log.debug("    %s", Frame.str_title())
            # apply all frames of this source to GStreamer pipeline
            for idx, frame in enumerate(frames):
                self.log.debug("%2d: %s", idx, frame)
                cropped = frame.cropped()
                alpha = frame.float_alpha()
                # transmit frame properties into mixing pipeline
                pad['xpos'].set(time, cropped[L])
                pad['ypos'].set(time, cropped[T])
                pad['width'].set(time, cropped[R] - cropped[L])
                pad['height'].set(time, cropped[B] - cropped[T])
                pad['alpha'].set(time, alpha)
                pad['zorder'].set(time, frame.zorder if alpha != 0 else -1)
                pad['croptop'].set(time, frame.crop[T])
                pad['cropleft'].set(time, frame.crop[L])
                pad['cropbottom'].set(time, frame.crop[B])
                pad['cropright'].set(time, frame.crop[R])
                # next frame time
                time += self.frame_time
            self.frames[source] = None
        self.dirty = False
