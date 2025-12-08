import logging
from gi.repository import Gtk


class UiBuilder(object):

    def __init__(self, uifile):
        if not hasattr(self, 'log'):
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

    def get_check_widget(self, widget_id):
        self.log.debug('loading widget "%s" from the .ui-File', widget_id)
        widget = self.builder.get_object(widget_id)
        if not widget:
            self.log.error(
                'could not load required widget "%s" from the .ui-File',
                widget_id
            )
            raise Exception('Widget not found in .ui-File')

        return widget

    def load_check_widget(self, widget_id, ui_file):
        builder = Gtk.Builder()
        builder.add_from_file(ui_file)

        self.log.debug(
            'loading widget "%s" from extra .ui-File "%s"', widget_id, ui_file)
        widget = builder.get_object(widget_id)
        if not widget:
            self.log.error(
                'could not load required widget "%s" from extra .ui-File "%s"',
                widget_id
            )
            raise Exception('Widget not found in .ui-File "%s"', ui_file)

        return widget
