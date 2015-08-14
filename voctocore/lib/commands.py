#!/usr/bin/python3
import logging
import json


from lib.config import Config
from lib.videomix import CompositeModes

class ControlServerCommands():
	def __init__(self, pipeline):
		self.log = logging.getLogger('ControlServerCommands')

		self.pipeline = pipeline
		self.sources = Config.getlist('mix', 'sources')
		self.blankersources = Config.getlist('stream-blanker', 'sources')

	def decodeSourceName(self, src_name_or_id):
		if isinstance(src_name_or_id, str):
			try:
				return self.sources.index(src_name_or_id)
			except Exception as e:
				raise IndexError("source %s unknown" % src_name_or_id)

		if src_name_or_id < 0 or src_name_or_id >= len(self.sources):
			raise IndexError("source %s unknown" % src_name_or_id)

	def encodeSourceName(self, src_id):
		try:
			return self.sources[src_id]
		except Exception as e:
			raise IndexError("source %s unknown" % src_id)

	def decodeBlankerSourceName(self, src_name_or_id):
		if isinstance(src_name_or_id, str):
			try:
				return self.blankersources.index(src_name_or_id)
			except Exception as e:
				raise IndexError("source %s unknown" % src_name_or_id)

		if src_name_or_id < 0 or src_name_or_id >= len(self.blankersources):
			raise IndexError("source %s unknown" % src_name_or_id)

	def encodeBlankerSourceName(self, src_id):
		try:
			return self.blankersources[src_id]
		except Exception as e:
			raise IndexError("source %s unknown" % src_id)


	def message(self, *args):
		return True

	def set_video_a(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.vmix.setVideoSourceA(src_id)
		return True

	def get_video_a(self):
		src_id = self.pipeline.vmix.getVideoSourceA()
		return (True, self.encodeSourceName(src_id))

	def set_video_b(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.vmix.setVideoSourceB(src_id)
		return True

	def get_video_b(self):
		src_id = self.pipeline.vmix.getVideoSourceB()
		return (True, self.encodeSourceName(src_id))

	def set_audio(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.amix.setAudioSource(src_id)
		return True

	def get_audio(self):
		src_id = self.pipeline.amix.getAudioSource()
		return (True, self.encodeSourceName(src_id))

	def set_composite_mode(self, composite_mode):
		try:
			mode = CompositeModes[composite_mode]
		except KeyError as e:
			raise KeyError("composite-mode %s unknown" % composite_mode)

		self.pipeline.vmix.setCompositeMode(mode)
		return True

	def get_composite_mode(self):
		try:
			mode = self.pipeline.vmix.getCompositeMode()
			return (True, mode.name)
		except Exception as e:
			raise KeyError("composite-mode %s unknown" % mode)

	def set_stream_status(self, *args):
		try:
			if args[0] == "live":
				self.pipeline.streamblanker.setBlankSource(None)
				return True
			elif args [0] == "blank":
				src_id = self.decodeBlankerSourceName(args[1])
				self.pipeline.streamblanker.setBlankSource(src_id)
				return True
			else:
				return (False, "invocation: set_stream_status (live | blank <mode>)")
		except IndexError as e:
			return (False, "invocation: set_stream_status (live | blank <mode>)")

	def get_stream_status(self):
		if self.pipeline.streamblanker.blankSource is None:
			return (True, "live")

		name = self.encodeBlankerSourceName(self.pipeline.streamblanker.blankSource)
		return (True, "blank " + name)

	def get_config(self):
		confdict = {k: dict(v) for k, v in dict(Config).items()}
		return (True, json.dumps(confdict))

