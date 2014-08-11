#!/usr/bin/python3
from gi.repository import GObject, Gst

class ShmSrc(Gst.Bin):
	def __init__(self, socket, caps):
		super().__init__()

		# Create elements
		self.shmsrc = Gst.ElementFactory.make('shmsrc', None)
		self.caps = Gst.ElementFactory.make('capsfilter', None)

		# Add elements to Bin
		self.add(self.shmsrc)
		self.add(self.caps)

		# Set properties
		self.shmsrc.set_property('socket-path', socket)
		self.shmsrc.set_property('is-live', True)
		self.shmsrc.set_property('do-timestamp', True)

		self.caps.set_property('caps', caps)
		self.shmsrc.link(self.caps)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.caps.get_static_pad('src'))
		)
