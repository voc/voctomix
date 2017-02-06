from gi.repository import Gtk

from lib.config import Config


if hasattr(Gtk, "ShortcutsWindow"):
    def show_shortcuts(win):
        shortcuts_window = ShortcutsWindow(win)
        shortcuts_window.show()

    class ShortcutsWindow(Gtk.ShortcutsWindow):
        def __init__(self, win):
            Gtk.ShortcutsWindow.__init__(self)
            self.build()
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            self.set_transient_for(win)
            self.set_modal(True)

        def build(self):
            section = Gtk.ShortcutsSection()
            section.show()

            compose_group = Gtk.ShortcutsGroup(title="Composition modes")
            compose_group.show()
            for accel, desc in [("F1", "Select fullscreen mode"),
                                ("F2", "Select Picture in Picture mode"),
                                ("F3", "Select  Side-by-Side Equal mode"),
                                ("F4", "Select  Side-by-Side Preview mode")]:
                short = Gtk.ShortcutsShortcut(title=desc, accelerator=accel)
                short.show()
                compose_group.add(short)
            section.add(compose_group)

            source_group = Gtk.ShortcutsGroup(title="Source Selection")
            source_group.show()
            num = len(Config.getlist('mix', 'sources'))
            source_items = [
                ("1...{}".format(num),
                 "Select Source as A-Source"),
                ("<ctrl>1...<ctrl>{}".format(num),
                 "Select Source as B-Source"),
                ("<alt>1...<alt>{}".format(num),
                 "Select Source as Fullscreen")
            ]
            for accel, desc in source_items:
                short = Gtk.ShortcutsShortcut(title=desc, accelerator=accel)
                short.show()
                source_group.add(short)
            section.add(source_group)

            if Config.getboolean('misc', 'cut'):
                other_group = Gtk.ShortcutsGroup(title="Other")
                other_group.show()
                short = Gtk.ShortcutsShortcut(title="Send Cut message",
                                              accelerator="t")
                short.show()
                other_group.add(short)
                section.add(other_group)

            self.add(section)
else:
    def show_shortcuts(win):
        pass
