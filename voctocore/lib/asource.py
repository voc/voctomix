#!/usr/bin/python3
import logging
from gi.repository import Gst

from lib.config import Config
from lib.tcpsingleconnection import TCPSingleConnection

class ASource(TCPSingleConnection):
	def __init__(self, name, port):
		self.log = logging.getLogger('ASource['+name+']')
		super().__init__(port)

		self.name = name

	def on_accepted(self, conn, addr):
		pipeline = """
			fdsrc fd={fd} !
			matroskademux !
			{acaps} !
			interaudiosink channel=audio_{name}
		""".format(
			fd=conn.fileno(),
			name=self.name,
			acaps=Config.get('mix', 'audiocaps')
		)

		self.log.debug('Launching Source-Pipeline:\n%s', pipeline)
		self.receiverPipeline = Gst.parse_launch(pipeline)

		self.log.debug('Binding End-of-Stream-Signal on Source-Pipeline')
		self.receiverPipeline.bus.add_signal_watch()
		self.receiverPipeline.bus.connect("message::eos", self.on_eos)
		self.receiverPipeline.bus.connect("message::error", self.on_error)

		self.all_audio_caps = Gst.Caps.from_string('audio/x-raw')
		self.audio_caps = Gst.Caps.from_string(Config.get('mix', 'audiocaps'))

		demux = self.receiverPipeline.get_by_name('demux')
		demux.connect('pad-added', self.on_pad_added)

		self.receiverPipeline.set_state(Gst.State.PLAYING)

	def on_pad_added(self, demux, src_pad):
		caps = src_pad.query_caps(None)
		self.log.debug('demuxer added pad w/ caps: %s', caps.to_string())
		if caps.can_intersect(self.all_audio_caps):
			self.log.debug('new demuxer-pad is a audio-pad, testing against configured audio-caps')
			if not caps.can_intersect(self.audio_caps):
				self.log.warning('the incoming connection presented a video-stream that is not compatible to the configured caps')
				self.log.warning('   incoming caps:   %s', caps.to_string())
				self.log.warning('   configured caps: %s', self.audio_caps.to_string())

	def on_eos(self, bus, message):
		self.log.debug('Received End-of-Stream-Signal on Source-Pipeline')
		if self.currentConnection is not None:
			self.disconnect()

	def on_error(self, bus, message):
		self.log.debug('Received Error-Signal on Source-Pipeline')
		(error, debug) = message.parse_error()
		self.log.debug('Error-Details: #%u: %s', error.code, debug)

		if self.currentConnection is not None:
			self.disconnect()

	def disconnect(self):
		self.receiverPipeline.set_state(Gst.State.NULL)
		self.receiverPipeline = None
		self.close_connection()
