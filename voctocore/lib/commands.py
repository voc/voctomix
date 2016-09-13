import logging
import json
import inspect

from lib.config import Config
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
		"""sends a message through the control-server, which can be received by
		user-defined scripts. does not change the state of the voctocore."""
		return NotifyResponse('message', *args)

	def help(self):
		helplines = []

		helplines.append("Commands:")
		for name, func in ControlServerCommands.__dict__.items():
			if name[0] == '_':
				continue

			if not func.__code__:
				continue

			params = inspect.signature(func).parameters
			params = [str(info) for name, info in params.items()]
			params = ', '.join(params[1:])

			command_sig = '\t' + name

			if params:
				command_sig += ': '+params

			if func.__doc__:
				command_sig += '\n'+'\n'.join(
					['\t\t'+line.strip() for line in func.__doc__.splitlines()])+'\n'

			helplines.append(command_sig)

		helplines.append('\t'+'quit / exit')

		helplines.append("\n")
		helplines.append("Source-Names:")
		for source in self.sources:
			helplines.append("\t"+source)

		helplines.append("\n")
		helplines.append("Stream-Blanker Sources-Names:")
		for source in self.blankerSources:
			helplines.append("\t"+source)

		return OkResponse("\n".join(helplines))


	def _get_audio_status(self):
		src_id = self.pipeline.amix.getAudioSource()
		return encodeName(self.sources, src_id)

	def get_audio(self):
		"""gets the name of the current audio-source"""
		status = self._get_audio_status()
		return OkResponse('audio_status', status)

	def set_audio(self, src_name_or_id):
		"""sets the audio-source to the supplied source-name or source-id"""
		src_id = decodeName(self.sources, src_name_or_id)
		self.pipeline.amix.setAudioSource(src_id)

		status = self._get_audio_status()
		return NotifyResponse('audio_status', status)


	def get_scene(self):
		"""gets the name of the current scene"""
		scene = self.pipeline.vmix.getScene()
		return OkResponse('audio_scene', scene)

	def set_scene(self, scene_name):
		"""sets the scene to the supplied scene-name"""
		self.pipeline.vmix.setScene(scene_name)

		scene = self.pipeline.vmix.getScene()
		return NotifyResponse('video_scene', scene)


	def _get_stream_status(self):
		blankSource = self.pipeline.streamblanker.blankSource
		if blankSource is None:
			return ('live',)

		return 'blank', encodeName(self.blankerSources, blankSource)

	def get_stream_status(self):
		"""gets the current streamblanker-status"""
		status = self._get_stream_status()
		return OkResponse('stream_status', *status)

	def set_stream_blank(self, source_name_or_id):
		"""sets the streamblanker-status to blank with the specified
		blanker-source-name or -id"""
		src_id = decodeName(self.blankerSources, source_name_or_id)
		self.pipeline.streamblanker.setBlankSource(src_id)

		status = self._get_stream_status()
		return NotifyResponse('stream_status', *status)

	def set_stream_live(self):
		"""sets the streamblanker-status to live"""
		self.pipeline.streamblanker.setBlankSource(None)

		status = self._get_stream_status()
		return NotifyResponse('stream_status', *status)


	def get_config(self):
		"""returns the parsed server-config"""
		confdict = {header: dict(section) for header, section in dict(Config).items()}
		return OkResponse('server_config', json.dumps(confdict))
