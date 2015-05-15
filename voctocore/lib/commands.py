#!/usr/bin/python3
import logging

from lib.config import Config
from lib.videomix import CompositeModes

class ControlServerCommands():
	def __init__(self, pipeline):
		self.log = logging.getLogger('ControlServerCommands')

		self.pipeline = pipeline
		self.sources = Config.getlist('mix', 'sources')

	def decodeSourceName(self, src_name_or_id):
		if isinstance(src_name_or_id, str):
			try:
				return self.sources.index(src_name_or_id)
			except Exception as e:
				raise IndexError("source %s unknown" % src_name_or_id)

		if src_name_or_id < 0 or src_name_or_id >= len(self.sources):
			raise IndexError("source %s unknown" % src_name_or_id)


	def set_video_a(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.vmix.setVideoSourceA(src_id)
		return True

	def set_video_b(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.vmix.setVideoSourceB(src_id)
		return True

	def set_audio(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.amix.setAudioSource(src_id)
		return True

	def set_composite_mode(self, composite_mode):
		try:
			mode = CompositeModes[composite_mode]
		except KeyError as e:
			raise KeyError("composite-mode %s unknown" % composite_mode)

		self.pipeline.vmix.setCompositeMode(mode)
		return True
