#!/usr/bin/python3
import os
import sys
import gi
import signal
import argparse
import socket

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstNet, GObject

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])


class Source(object):

    def __init__(self, settings):
        pipeline = """
            ximagesrc
                use-damage=0
                startx=0 starty=0 endx=1919 endy=1079 !
            queue !
            videoscale !
            videorate !
            timeoverlay !
            videoconvert !
            video/x-raw,format=I420,width={WIDTH},height={HEIGHT},
                framerate={FRAMERATE}/1,pixel-aspect-ratio=1/1 !
            queue !
            mux.

            pulsesrc !
            audio/x-raw,format=S16LE,channels=2,rate={AUDIORATE},
                layout=interleaved !
            queue !
            mux.

            matroskamux name=mux !
            tcpclientsink host={IP} port=10000
        """.format_map(settings)

        self.clock = GstNet.NetClientClock.new('voctocore',
                                               settings['IP'], 9998,
                                               0)
        print('obtained NetClientClock from host', self.clock)

        print('waiting for NetClientClock to sync…')
        self.clock.wait_for_sync(Gst.CLOCK_TIME_NONE)

        print('starting pipeline ' + pipeline)
        self.senderPipeline = Gst.parse_launch(pipeline)
        self.senderPipeline.use_clock(self.clock)
        self.src = self.senderPipeline.get_by_name('src')

        # Binding End-of-Stream-Signal on Source-Pipeline
        self.senderPipeline.bus.add_signal_watch()
        self.senderPipeline.bus.connect("message::eos", self.on_eos)
        self.senderPipeline.bus.connect("message::error", self.on_error)

        print("playing")
        self.senderPipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        print('Received EOS-Signal')
        sys.exit(1)

    def on_error(self, bus, message):
        print('Received Error-Signal')
        (error, debug) = message.parse_error()
        print('Error-Details: #%u: %s' % (error.code, debug))
        sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description='Voctocore Remote-Source')
    parser.add_argument('host')

    args = parser.parse_args()
    print('Resolving hostname ' + args.host)
    addrs = [str(i[4][0]) for i in socket.getaddrinfo(args.host, None)]
    if len(addrs) == 0:
        print('Found no IPs')
        sys.exit(1)

    print('Using IP ' + addrs[0])

    settings = {}

    for prefix in ['default-', '']:
        config = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              '..', '{}config.sh'.format(prefix))
        if not os.path.exists(config):
            continue

        with open(config, 'r') as config:
            lines = [line.strip() for line in config if line[0] != '#']
            pairs = [line.split('=', 1) for line in lines]
            for pair in pairs:
                settings[pair[0]] = pair[1]

    if not ('FRAMERATE' in settings and
            'WIDTH' in settings and
            'HEIGHT' in settings and
            'AUDIORATE' in settings):
        print("Config needs: FRAMERATE, WIDTH, HEIGHT, and AUDIORATE")
        return

    settings['IP'] = addrs[0]

    src = Source(settings)
    mainloop = GObject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Terminated via Ctrl-C')


if __name__ == '__main__':
    main()
