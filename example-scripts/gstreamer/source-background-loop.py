#!/usr/bin/env python3
import os
import sys
import gi
import signal

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])


class LoopSource(object):

    def __init__(self, settings):
        # it works much better with a local file
        pipeline = """
            uridecodebin name=src
                uri=http://c3voc.mazdermind.de/testfiles/bg.ts !
            videoscale !
            videoconvert !
            video/x-raw,format=I420,width={WIDTH},height={HEIGHT},
                framerate={FRAMERATE}/1,pixel-aspect-ratio=1/1 !
            matroskamux !
            tcpclientsink host=localhost port=16000
        """.format_map(settings)

        print('starting pipeline ' + pipeline)
        self.senderPipeline = Gst.parse_launch(pipeline)
        self.src = self.senderPipeline.get_by_name('src')

        # Binding End-of-Stream-Signal on Source-Pipeline
        self.senderPipeline.bus.add_signal_watch()
        self.senderPipeline.bus.connect("message::eos", self.on_eos)
        self.senderPipeline.bus.connect("message::error", self.on_error)

        print("playing")
        self.senderPipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        print('Received EOS-Signal, Seeking to start')
        self.src.seek(
            1.0,                 # rate (float)
            Gst.Format.TIME,     # format (Gst.Format)
            Gst.SeekFlags.FLUSH,  # flags (Gst.SeekFlags)
            Gst.SeekType.SET,    # start_type (Gst.SeekType)
            0,                   # start (int)
            Gst.SeekType.NONE,   # stop_type (Gst.SeekType)
            0                    # stop (int)
        )

    def on_error(self, bus, message):
        print('Received Error-Signal')
        (error, debug) = message.parse_error()
        print('Error-Details: #%u: %s' % (error.code, debug))
        sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    config = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '../config.sh')
    with open(config, 'r') as config:
        lines = [line.strip() for line in config if line[0] != '#']
        pairs = [line.split('=', 1) for line in lines]
        settings = {pair[0]: pair[1] for pair in pairs}

    src = LoopSource(settings)

    mainloop = GObject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Terminated via Ctrl-C')


if __name__ == '__main__':
    main()
