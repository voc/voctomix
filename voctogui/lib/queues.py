#!/usr/bin/env python3
import logging
import os
import json
from gi.repository import Gtk, Gst, GLib

from lib.config import Config
from lib.uibuilder import UiBuilder
import lib.connection as Connection

class QueuesWindowController():

    timer_resolution = 1.0

    def __init__(self,uibuilder):
        self.log = logging.getLogger('QueuesWindowController')

        self.win = uibuilder.get_check_widget('queue_win')
        self.store = uibuilder.get_check_widget('queue_store')
        Connection.on('queue_report', self.on_queue_report)

    def on_queue_report(self, *report):
        report = json.loads("".join(report))
        self.store.clear()
        for queue, time in report.items():
            self.store.append((queue, time / Gst.SECOND))

    def show(self,visible=True):
        if visible:
            Connection.send('report_queues')
            GLib.timeout_add(self.timer_resolution * 1000, self.do_timeout)
            self.win.show()
        else:
            self.win.hide()

    def do_timeout(self):
        Connection.send('report_queues')
        return self.win.is_visible()
