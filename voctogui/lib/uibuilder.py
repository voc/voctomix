import gi
import logging
from gi.repository import Gtk, Gst


class UiBuilder(object):

    def __init__(self, uifile):
        if not self.log:
            self.log = logging.getLogger('UiBuilder')

        self.uifile = uifile

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.uifile)

    def find_widget_recursive(self, widget, name):
        widget = self._find_widget_recursive(widget, name)
        if not widget:
            self.log.error(
                'could find required widget "%s" by ID inside the parent %s',
                name,
                str(widget)
            )
            raise Exception('Widget not found in parent')

        return widget

    def _find_widget_recursive(self, widget, name):
        if Gtk.Buildable.get_name(widget) == name:
            return widget

        if hasattr(widget, 'get_children'):
            for child in widget.get_children():
                widget = self._find_widget_recursive(child, name)
                if widget:
                    return widget

        return None

    def get_check_widget(self, widget_id, clone=False):
        if clone:
            builder = Gtk.Builder()
            builder.add_from_file(self.uifile)
        else:
            builder = self.builder

        self.log.debug('loading widget "%s" from the .ui-File', widget_id)
        widget = builder.get_object(widget_id)
        if not widget:
            self.log.error(
                'could not load required widget "%s" from the .ui-File',
                widget_id
            )
            raise Exception('Widget not found in .ui-File')

        return widget
