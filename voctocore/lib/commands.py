#!/usr/bin/python3
import logging

from lib.config import Config
from lib.video.mix import CompositeModes

class ControlServerCommands():
	log = logging.getLogger('ControlServerCommands')

	pipeline = None
	vnames = []

	def __init__(self, pipeline):
		self.pipeline = pipeline
		self.vnames = Config.getlist('sources', 'video')

	def decodeVideoSrcName(self, src_name_or_id):
		if isinstance(src_name_or_id, str):
			try:
				return self.vnames.index(src_name_or_id)
			except Exception as e:
				raise IndexError("video-source %s unknown" % src_name_or_id)

		if src_name_or_id < 0 or src_name_or_id >= len(self.vnames):
			raise IndexError("video-source %s unknown" % src_name_or_id)


	def set_video_a(self, src_name_or_id):
		src_id = self.decodeVideoSrcName(src_name_or_id)
		self.pipeline.vmixer.setVideoA(src_id)
		return True

	def set_video_b(self, src_name_or_id):
		src_id = self.decodeVideoSrcName(src_name_or_id)
		self.pipeline.vmixer.setVideoB(src_id)
		return True

	def set_composite_mode(self, composite_mode):
		try:
			mode = CompositeModes[composite_mode]
		except KeyError as e:
			raise KeyError("composite-mode %s unknown" % composite_mode)

		self.pipeline.vmixer.setCompositeMode(mode)
		return True
