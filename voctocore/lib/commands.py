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

	# Commands are defined below. Errors are sent to the clients by throwing
	# exceptions, they will be turned into messages outside.

	def fetch(self, command):
		if command not in ['set', 'get', 'message', 'signal']:
			raise Exception("unknown command")
		return getattr(self, command)

	def message(self, *args):
		return " ".join(args), True

	def signal(self, *args):
		return "", True

	def get(self, subcommand, *args, signal=False):
		return getattr(self, "_get_"+subcommand)(*args), signal

	def set(self, subcommand, *args):
		getattr(self, "_set_"+subcommand)(*args)
		return self.get(subcommand, *args, signal=True)

	def _get_video(self, target, _=None):
		if target not in ['a', 'b']:
			raise Exception("invalid video source name: 'a' or 'b' expected.")
		cmd = "getVideoSource" + target.upper()
		src_id = getattr(self.pipeline.vmix, cmd)()
		return self.encodeSourceName(src_id)

	def _set_video(self, target, src_name_or_id):
		if target not in ['a', 'b']:
			raise Exception("invalid video source name: 'a' or 'b' expected.")
		src_id = self.decodeSourceName(src_name_or_id)
		getattr(self.pipeline.vmix, 'setVideoSource' + target.upper())(src_id)

	def _set_audio(self, src_name_or_id):
		src_id = self.decodeSourceName(src_name_or_id)
		self.pipeline.amix.setAudioSource(src_id)

	def _get_audio(self, _=None):
		src_id = self.pipeline.amix.getAudioSource()
		return self.encodeSourceName(src_id)

	def _set_composite(self, composite_mode):
		try:
			mode = CompositeModes[composite_mode]
		except KeyError as e:
			raise KeyError("composite-mode %s unknown" % composite_mode)

		self.pipeline.vmix.setCompositeMode(mode)

	def _get_composite(self, _=None):
		try:
			mode = self.pipeline.vmix.getCompositeMode()
			return mode.name
		except Exception as e:
			raise KeyError("composite-mode %s unknown" % mode)

	def _set_status(self, *args):
		try:
			if args[0] == "live":
				self.pipeline.streamblanker.setBlankSource(None)
			elif args [0] == "blank":
				src_id = self.decodeBlankerSourceName(args[1])
				self.pipeline.streamblanker.setBlankSource(src_id)
			else:
				raise IndexError()
		except IndexError as e:
			raise Exception("invocation: set_status (live | blank <mode>)")

	def _get_status(self, *args):
		if self.pipeline.streamblanker.blankSource is None:
			return "live"

		name = self.encodeBlankerSourceName(self.pipeline.streamblanker.blankSource)
		return "blank " + name

	def _get_config(self):
		confdict = {k: dict(v) for k, v in dict(Config).items()}
		return json.dumps(confdict)

