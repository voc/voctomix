#!/usr/bin/python3
import logging
import json

from lib.config import Config
from lib.videomix import CompositeModes
from lib.response import NotifyResponse, OkResponse

def decodeName(items, name_or_id):
	try:
		name_or_id = int(name_or_id)
		if name_or_id < 0 or name_or_id >= len(items):
			raise IndexError("unknown index %d" % name_or_id)

		return name_or_id

	except ValueError as e:
		try:
			return items.index(name_or_id)

		except ValueError as e:
			raise IndexError("unknown name %s" % name_or_id)

def decodeEnumName(enum, name_or_id):
	try:
		name_or_id = int(name_or_id)
		if name_or_id < 0 or name_or_id >= len(enum):
			raise IndexError("unknown index %d" % name_or_id)

		return name_or_id

	except ValueError as e:
		try:
			return enum[name_or_id]

		except KeyError as e:
			raise IndexError("unknown name %s" % name_or_id)

def encodeName(items, id):
	try:
		return items[id]
	except IndexError as e:
		raise IndexError("unknown index %d" % id)

def encodeEnumName(enum, id):
	try:
		return enum(id).name
	except ValueError as e:
		raise IndexError("unknown index %d" % id)

class ControlServerCommands(object):
	def __init__(self, pipeline):
		self.log = logging.getLogger('ControlServerCommands')

		self.pipeline = pipeline

		self.sources = Config.getlist('mix', 'sources')
		self.blankerSources = Config.getlist('stream-blanker', 'sources')

	# Commands are defined below. Errors are sent to the clients by throwing
	# exceptions, they will be turned into messages outside.

	def message(self, *args):
		return NotifyResponse('message', *args)


	def _get_video_status(self):
		a = encodeName( self.sources, self.pipeline.vmix.getVideoSourceA() )
		b = encodeName( self.sources, self.pipeline.vmix.getVideoSourceB() )
		return [a, b]

	def get_video(self):
		status = self._get_video_status()
		return OkResponse('video_status', *status)

	def set_video_a(self, src_name_or_id):
		src_id = decodeName(self.sources, src_name_or_id)
		self.pipeline.vmix.setVideoSourceA(src_id)

		status = self._get_video_status()
		return NotifyResponse('video_status', *status)

	def set_video_b(self, src_name_or_id):
		src_id = decodeName(self.sources, src_name_or_id)
		self.pipeline.vmix.setVideoSourceB(src_id)

		status = self._get_video_status()
		return NotifyResponse('video_status', *status)


	def _get_audio_status(self):
		src_id = self.pipeline.amix.getAudioSource()
		return encodeName(self.sources, src_id)

	def get_audio(self):
		status = self._get_audio_status()
		return OkResponse('audio_status', status)

	def set_audio(self, src_name_or_id):
		src_id = decodeName(self.sources, src_name_or_id)
		self.pipeline.amix.setAudioSource(src_id)

		status = self._get_audio_status()
		return NotifyResponse('audio_status', status)


	def _get_composite_status(self):
		mode = self.pipeline.vmix.getCompositeMode()
		return encodeEnumName(CompositeModes, mode)

	def get_composite_mode(self):
		status = self._get_composite_status()
		return OkResponse('composite_mode', status)

	def set_composite_mode(self, mode_name_or_id):
		mode = decodeEnumName(CompositeModes, mode_name_or_id)
		self.pipeline.vmix.setCompositeMode(mode)

		status = self._get_composite_status()
		return NotifyResponse('composite_mode', status)

	def set_videos_and_composite(self, src_a_name_or_id, src_b_name_or_id, mode_name_or_id):
		if src_a_name_or_id != '*':
			src_a_id = decodeName(self.sources, src_a_name_or_id)
			self.pipeline.vmix.setVideoSourceA(src_a_id)

		if src_b_name_or_id != '*':
			src_b_id = decodeName(self.sources, src_b_name_or_id)
			self.pipeline.vmix.setVideoSourceB(src_b_id)

		if mode_name_or_id != '*':
			mode = decodeEnumName(CompositeModes, mode_name_or_id)
			self.pipeline.vmix.setCompositeMode(mode)

		composite_status = self._get_composite_status()
		video_status = self._get_video_status()

		return [
			NotifyResponse('composite_mode', composite_status),
			NotifyResponse('video_status', *video_status)
		]


	def _get_stream_status(self):
		blankSource = self.pipeline.streamblanker.blankSource
		if blankSource is None:
			return ('live',)

		return 'blank', encodeName(self.blankerSources, blankSource)

	def get_stream_status(self):
		status = self._get_stream_status()
		return OkResponse('stream_status', *status)

	def set_stream_blank(self, source_name_or_id):
		src_id = decodeName(self.blankerSources, source_name_or_id)
		self.pipeline.streamblanker.setBlankSource(src_id)

		status = self._get_stream_status()
		return NotifyResponse('stream_status', *status)

	def set_stream_live(self):
		self.pipeline.streamblanker.setBlankSource(None)

		status = self._get_stream_status()
		return NotifyResponse('stream_status', *status)


	def get_config(self):
		confdict = {header: dict(section) for header, section in dict(Config).items()}
		return OkResponse('server_config', json.dumps(confdict))
