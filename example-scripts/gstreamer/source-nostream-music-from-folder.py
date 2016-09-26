#!/usr/bin/env python3
import os
import sys
import gi
import signal
import random
import argparse
import logging
import pyinotify

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

# init GObject & Co. before importing local classes
GObject.threads_init()
Gst.init([])


class Directory(object):

    def __init__(self, path):
        self.log = logging.getLogger('Directory')
        self.path = path
        self.scheduled = False
        self.rescan()

        self.log.debug('setting up inotify watch for %s', self.path)
        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(
            wm,
            timeout=10,
            default_proc_fun=self.inotify_callback
        )

        wm.add_watch(
            self.path,
            # pyinotify.ALL_EVENTS,
            pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY,
            rec=True
        )

        GLib.io_add_watch(
            notifier._fd,
            GLib.IO_IN,
            self.io_callback,
            notifier
        )

    def inotify_callback(self, notifier):
        self.log.info('inotify callback %s: %s',
                      notifier.maskname, notifier.pathname)
        if not self.scheduled:
            self.scheduled = True
            GLib.timeout_add(100, self.rescan)
        return True

    def io_callback(self, source, condition, notifier):
        notifier.process_events()
        while notifier.check_events():
            notifier.read_events()
            notifier.process_events()

        return True

    def is_playable_file(self, filepath):
        root, ext = os.path.splitext(filepath)
        return ext in ['.mp3', '.ogg', '.oga', '.wav', '.m4a',
                       '.flac', 'self.opus']

    def rescan(self):
        self.log.info('scanning directory %s', self.path)
        self.scheduled = False

        all_files = []

        for root, dirs, files in os.walk(self.path):
            files = filter(self.is_playable_file, files)
            files = map(lambda f: os.path.join(root, f), files)
            files = list(files)

            self.log.debug('found directory %s: %u playable file(s)',
                           root, len(files))
            all_files.extend(files)

        self.log.info('found %u playable files', len(all_files))
        self.files = all_files

    def get_random_file(self):
        return random.choice(self.files)

    def get_random_uri(self):
        return 'file://' + self.get_random_file()


class LoopSource(object):

    def __init__(self, directory):
        self.log = logging.getLogger('LoopSource')
        self.directory = directory

        pipeline = """
            audioresample name=join !
            audioconvert !
            audio/x-raw,format=S16LE,channels=2,rate=48000,
                layout=interleaved !
            matroskamux !
            tcpclientsink host=localhost port=18000
        """

        # Parsing Pipeline
        self.log.debug('creating pipeline\n%s', pipeline)
        self.pipeline = Gst.parse_launch(pipeline)

        # Selecting inital URI
        inital_uri = self.directory.get_random_uri()
        self.log.info('initial track %s', inital_uri)

        # Create decoder-element
        self.src = Gst.ElementFactory.make('uridecodebin', None)
        self.src.set_property('uri', inital_uri)
        self.src.connect('pad-added', self.on_pad_added)
        self.pipeline.add(self.src)

        # Save pad on the Join-Element
        self.joinpad = self.pipeline.get_by_name('join').get_static_pad('sink')

        # Binding End-of-Stream-Signal on Source-Pipeline
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message::eos", self.on_eos)
        self.pipeline.bus.connect("message::error", self.on_error)

        self.log.debug('setting pipeline to playing')
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_pad_added(self, src, pad):
        self.log.debug('new pad on decoder, setting pad-probe')
        pad.add_probe(
            Gst.PadProbeType.EVENT_DOWNSTREAM | Gst.PadProbeType.BLOCK,
            self.on_pad_event
        )
        if self.joinpad.is_linked():
            self.log.debug('unlinking with joinpad')
            self.joinpad.unlink(self.joinpad.get_peer())

        clock = self.pipeline.get_clock()
        if clock:
            runtime = clock.get_time() - self.pipeline.get_base_time()
            self.log.debug('setting pad offset to pipeline runtime: %sns',
                           runtime)
            pad.set_offset(runtime)

        self.log.debug('linking with joinpad')
        pad.link(self.joinpad)

    def on_pad_event(self, pad, info):
        event = info.get_event()
        self.log.debug('event %s on pad %s', event.type, pad)

        if event.type == Gst.EventType.EOS:
            self.log.debug('scheduling next track and dropping EOS-Event')
            GObject.idle_add(self.next_track)
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.PASS

    def next_track(self):
        next_uri = self.directory.get_random_uri()
        self.log.info('next track %s', next_uri)

        self.src.set_state(Gst.State.READY)
        self.src.set_property('uri', next_uri)
        self.src.set_state(Gst.State.PLAYING)
        return False

    def on_eos(self, bus, message):
        self.log.info('received EOS-Event on bus, exiting')
        sys.exit(1)

    def on_error(self, bus, message):
        self.log.warning('received Error-Event on bus, exiting')
        (error, debug) = message.parse_error()
        self.log.warning('Error-Details: #%u: %s', error.code, debug)
        sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description='Voctocore Music-Source')
    parser.add_argument('directory')

    parser.add_argument('-v|-vv', '--verbose', action='count', default=0,
                        help="Also print INFO and DEBUG messages.")

    args = parser.parse_args()

    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format='%(levelname)8s %(name)s: %(message)s'
    )

    directory = Directory(args.directory)
    src = LoopSource(directory)

    mainloop = GObject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Terminated via Ctrl-C')


if __name__ == '__main__':
    main()
