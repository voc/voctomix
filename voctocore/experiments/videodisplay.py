#!/usr/bin/python3
from gi.repository import GObject, Gst

class VideomixerWithDisplay(Gst.Bin):
	def __init__(self):
		super().__init__()

		# Create elements
		self.secondsrc = Gst.ElementFactory.make('videotestsrc', None)
		self.mixer = Gst.ElementFactory.make('videomixer', None)
		self.ident = Gst.ElementFactory.make('identity', None)
		self.conv = Gst.ElementFactory.make('videoconvert', None)
		self.q1 = Gst.ElementFactory.make('queue', None)
		self.q2 = Gst.ElementFactory.make('queue', None)
		self.display = Gst.ElementFactory.make('ximagesink', None)

		# Add elements to Bin
		self.add(self.secondsrc)
		self.add(self.mixer)
		self.add(self.ident)
		self.add(self.conv)
		self.add(self.display)
		self.add(self.q1)
		self.add(self.q2)

		# Set properties
		self.secondsrc.set_property('pattern', 'ball')
		self.ident.set_property('sync', True)
		self.display.set_property('sync', False)

		# Request Pads
		self.firstpad = self.mixer.get_request_pad('sink_%u')
		self.secondpad = self.mixer.get_request_pad('sink_%u')

		# Set pad-properties
		self.secondpad.set_property('alpha', 0.75)
		self.secondpad.set_property('xpos', 50)
		self.secondpad.set_property('ypos', 50)

		# Link elements
		self.q1.get_static_pad('src').link(self.firstpad)

		self.q2.get_static_pad('src').link(self.secondpad)
		self.secondsrc.link_filtered(self.ident, Gst.Caps.from_string('video/x-raw,format=BGRA,width=400,height=400,framerate=25/1'))
		self.ident.link(self.q2)

		self.mixer.link(self.conv)
		self.conv.link(self.display)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.q1.get_static_pad('sink'))
		)
