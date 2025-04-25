from gi.repository import Gtk
from gi.repository.Gtk import Requisition

class VideoPreviewFrame(Gtk.Bin):
    """
    Custom helper class to force a specific size for a child widget
    """
    natural_width: int
    natural_height: int

    def __init__(self, natural_width: int, natural_height: int):
        super().__init__()
        self.natural_width = natural_width
        self.natural_height = natural_height

    def do_get_preferred_size(self) -> tuple[Requisition, Requisition]:
        natural_size = Requisition.new()
        natural_size.width = self.natural_width
        natural_size.height = self.natural_height
        return natural_size, natural_size

    def do_get_preferred_height(self) -> tuple[int, int]:
        return self.natural_height, self.natural_height

    def do_get_preferred_width(self) -> tuple[int, int]:
        return self.natural_width, self.natural_width
