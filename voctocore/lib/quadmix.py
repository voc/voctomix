#!/usr/bin/python3
import math, logging
from gi.repository import GLib, Gst

from lib.helper import iteratorHelper
from lib.config import Config

class QuadMix(Gst.Bin):
	log = logging.getLogger('QuadMix')
	previewbins = []
	mixerpads = []

	def __init__(self):
		super().__init__()

		caps = Gst.Caps.from_string(Config.get('mix', 'monitorcaps'))
		self.log.debug('parsing monitorcaps from config: %s', caps.to_string())
		struct = caps.get_structure(0)

		self.monitorSize = [struct.get_int('width')[1], struct.get_int('height')[1]]

		self.bgsrc = Gst.ElementFactory.make('videotestsrc', 'bgsrc')
		self.mixer = Gst.ElementFactory.make('videomixer', 'mixer')
		self.scale = Gst.ElementFactory.make('videoscale', 'scale')

		self.add(self.bgsrc)
		self.add(self.mixer)
		self.add(self.scale)

		self.bgsrc.link_filtered(self.mixer, caps)
		self.mixer.link_filtered(self.scale, caps)
		
		self.bgsrc.set_property('pattern', 'solid-color')
		self.bgsrc.set_property('foreground-color', 0x808080)

		self.add_pad(
			Gst.GhostPad.new('src', self.scale.get_static_pad('src'))
		)

	def request_mixer_pad(self):
		previewbin = QuadMixPreview()
		self.add(previewbin)
		self.previewbins.append(previewbin)

		srcpad = previewbin.get_static_pad('src')
		sinkpad = previewbin.get_static_pad('sink')

		mixerpad = self.mixer.get_request_pad('sink_%u')
		self.mixerpads.append(mixerpad)
		srcpad.link(mixerpad)

		ghostpad = Gst.GhostPad.new(mixerpad.get_name(), sinkpad)
		self.add_pad(ghostpad)
		return ghostpad

	def finalize(self):
		self.log.debug('all sources added, calculating layout')

		# number of placed sources
		count = len(self.previewbins)

		# coordinate of the cell where we place the next video
		place = [0, 0]
		
		# number of cells in the quadmix-monitor
		grid = [0, 0]
		grid[0] = math.ceil(math.sqrt(count))
		grid[1] = math.ceil(count / grid[0])

		# size of each cell in the quadmix-monitor
		cellSize = (
			self.monitorSize[0] / grid[0],
			self.monitorSize[1] / grid[1]
		)

		# report calculation results
		self.log.info('showing %u videosources in a %u×%u grid in a %u×%u px window, which gives cells of %u×%u px per videosource',
			count, grid[0], grid[1], self.monitorSize[0], self.monitorSize[1], cellSize[0], cellSize[1])

		# iterate over all video-sources
		for idx, previewbin in enumerate(self.previewbins):
			# ...
			srcpad = previewbin.get_static_pad('src')
			mixerpad = self.mixerpads[idx]

			# query the video-source caps and extract its size
			caps = srcpad.query_caps(None)
			capsstruct = caps.get_structure(0)
			srcSize = (
				capsstruct.get_int('width')[1],
				capsstruct.get_int('height')[1],
			)

			# calculate the ideal scale factor and scale the sizes
			f = max(srcSize[0] / cellSize[0], srcSize[1] / cellSize[1])
			scaleSize = (
				srcSize[0] / f,
				srcSize[1] / f,
			)

			# calculate the top/left coordinate
			coord = (
				place[0] * cellSize[0] + (cellSize[0] - scaleSize[0]) / 2,
				place[1] * cellSize[1] + (cellSize[1] - scaleSize[1]) / 2,
			)

			self.log.info('placing videosource %u of size %u×%u scaled by %u to %u×%u in a cell %u×%u px cell (%u/%u) at position (%u/%u)', 
				idx, srcSize[0], srcSize[1], f, scaleSize[0], scaleSize[1], cellSize[0], cellSize[1], place[0], place[1], coord[0], coord[1])

			# request a pad from the quadmixer and configure x/y position
			mixerpad.set_property('xpos', round(coord[0]))
			mixerpad.set_property('ypos', round(coord[1]))

			previewbin.set_size(scaleSize)
			previewbin.set_idx(idx)

			# increment grid position
			place[0] += 1
			if place[0] >= grid[0]:
				place[1] += 1
				place[0] = 0

	def set_active(self, target):
		for idx, previewbin in enumerate(self.previewbins):
			previewbin.set_active(target == idx)

class QuadMixPreview(Gst.Bin):
	log = logging.getLogger('QuadMixPreview')
	strokeWidth = 5

	def __init__(self):
		super().__init__()

		self.scale = Gst.ElementFactory.make('videoscale', 'scale')
		self.caps = Gst.ElementFactory.make('capsfilter', 'caps')
		self.cropbox = Gst.ElementFactory.make('videobox', 'cropbox')
		self.strokebox = Gst.ElementFactory.make('videobox', 'strokebox')
		self.textoverlay = Gst.ElementFactory.make('textoverlay', 'textoverlay')

		self.add(self.scale)
		self.add(self.caps)
		self.add(self.cropbox)
		self.add(self.strokebox)
		self.add(self.textoverlay)

		self.strokebox.set_property('fill', 'green')

		self.textoverlay.set_property('color', 0xFFFFFFFF)
		self.textoverlay.set_property('halignment', 'left')
		self.textoverlay.set_property('valignment', 'top')
		self.textoverlay.set_property('xpad', 10)
		self.textoverlay.set_property('ypad', 5)
		self.textoverlay.set_property('font-desc', 'sans 35')

		self.scale.link(self.caps)
		self.caps.link(self.cropbox)
		self.cropbox.link(self.strokebox)
		self.strokebox.link(self.textoverlay)

		self.set_active(False)

		# Add Ghost Pads
		self.add_pad(
			Gst.GhostPad.new('sink', self.scale.get_static_pad('sink'))
		)
		self.add_pad(
			Gst.GhostPad.new('src', self.textoverlay.get_static_pad('src'))
		)

	def set_size(self, scaleSize):
		caps = Gst.Caps.new_empty_simple('video/x-raw')
		caps.set_value('width', round(scaleSize[0]))
		caps.set_value('height', round(scaleSize[1]))
		self.caps.set_property('caps', caps)

	def set_idx(self, idx):
		self.textoverlay.set_property('text', str(idx))

	def set_active(self, active):
		self.log.info("switching active-state to %u", active)
		for side in ('top', 'left', 'right', 'bottom'):
			self.cropbox.set_property(side, self.strokeWidth if active else 0)
			self.strokebox.set_property(side, -self.strokeWidth if active else 0)

	def set_color(self, color):
		self.strokebox.set_property('fill', color)
