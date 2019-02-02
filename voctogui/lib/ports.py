#!/usr/bin/env python3
import logging
import os
import json
from gi.repository import Gtk, Gst, GLib

from lib.config import Config
from lib.uibuilder import UiBuilder
import lib.connection as Connection
from vocto.port import Port

# time interval to re-fetch queue timings
TIMER_RESOLUTION = 5.0


class PortsWindowController():

    def __init__(self, uibuilder):
        self.log = logging.getLogger('QueuesWindowController')

        # get related widgets
        self.win = uibuilder.get_check_widget('ports_win')
        self.store = uibuilder.get_check_widget('ports_store')
        self.scroll = uibuilder.get_check_widget('ports_scroll')

        # remember row iterators
        self.iterators = None

        # listen for queue_report from voctocore
        Connection.on('port_report', self.on_port_report)

    def on_port_report(self, *report):
        # read string report into dictonary
        report = json.loads("".join(report))
        # check if this is the initial report
        if not self.iterators:
            # append report as rows to treeview store and remember row iterators
            self.iterators = dict()
            for p in report:
                port = Port.from_str(p)
                print(port.port)
                self.iterators[port.port] = self.store.append((
                    port.name,
                    port.audio,
                    port.video,
                    "IN" if port.is_input() else "OUT",
                    port.port
                ))
        else:
            # just update values of second column
            for p in report:
                port = Port.from_str(p)
                it = self.iterators[port.port]
                self.store.set_value(it, 0, port.name)
                self.store.set_value(it, 1, port.audio)
                self.store.set_value(it, 2, port.video)
                self.store.set_value(it, 3, "IN" if port.is_input() else "OUT")
                self.store.set_value(it, 4, port.port)

    def show(self, visible=True):
        # check if widget is getting visible
        if visible:
            # request queue timing report from voctocore
            Connection.send('report_ports')
            # schedule repetition
            GLib.timeout_add(TIMER_RESOLUTION * 1000, self.do_timeout)
            # do the boring stuff
            self.win.show()
        else:
            self.win.hide()

    def do_timeout(self):
        # re-request queue report
        Connection.send('report_ports')
        # repeat if widget is visible
        return self.win.is_visible()
