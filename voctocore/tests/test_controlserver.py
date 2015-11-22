import unittest
from unittest import mock

from twisted.test import proto_helpers

from lib.controlserver import ControlServer
from lib.pipeline import Pipeline
from lib.videomix import CompositeModes, VideoMix
from lib.audiomix import AudioMix
from lib.streamblanker import StreamBlanker


class ControlServerTests(unittest.TestCase):

	def setUp(self):
		self.pipeline = mock.Mock(spec=Pipeline)
		self.pipeline.vmix = mock.Mock(spec=VideoMix)
		self.pipeline.amix = mock.Mock(spec=AudioMix)
		self.pipeline.streamblanker = mock.Mock(spec=StreamBlanker)
		self.factory = ControlServer(self.pipeline)

	def makeConnection(self):
		transport = proto_helpers.StringTransport()
		proto = self.factory.buildProtocol(('127.0.0.1', 0))
		proto.makeConnection(transport)
		return transport, proto

	def assertResponds(self, command, response):
		tr1, proto1 = self.makeConnection()
		tr2, proto2 = self.makeConnection()
		proto1.dataReceived(command)
		self.assertEqual(response, tr1.value())
		# Nothing should be sent to other connections
		self.assertEqual(b'', tr2.value())

	def assertNotifies(self, command, response):
		tr1, proto1 = self.makeConnection()
		tr2, proto2 = self.makeConnection()
		proto1.dataReceived(command)
		self.assertEqual(response, tr1.value())
		self.assertEqual(response, tr2.value())

	def test_quit(self):
		tr, proto = self.makeConnection()
		proto.dataReceived(b'quit\n')
		self.assertTrue(tr.disconnecting)

	def test_bad_command(self):
		self.assertResponds(b'no_such_command\n',
				    b'error unknown command no_such_command\n')

	def test_private_method(self):
		self.assertResponds(b'__init__ foo\n',
				    b'error unknown command __init__\n')

	def test_message(self):
		self.assertNotifies(b'message hello world\n',
				    b'message hello world\n')

	def test_get_video(self):
		self.pipeline.vmix.getVideoSourceA.return_value = 0
		self.pipeline.vmix.getVideoSourceB.return_value = 1
		tr, proto = self.makeConnection()
		self.assertResponds(b'get_video\n',
				    b'video_status cam1 cam2\n')

	def test_set_video_a(self):
		self.pipeline.vmix.getVideoSourceA.return_value = 1
		self.pipeline.vmix.getVideoSourceB.return_value = 0
		self.assertNotifies(b'set_video_a cam2\n',
				    b'video_status cam2 cam1\n')
		self.pipeline.vmix.setVideoSourceA.assert_called_once_with(1)

	def test_set_video_b(self):
		self.pipeline.vmix.getVideoSourceA.return_value = 1
		self.pipeline.vmix.getVideoSourceB.return_value = 0
		self.assertNotifies(b'set_video_b cam1\n',
				    b'video_status cam2 cam1\n')
		self.pipeline.vmix.setVideoSourceB.assert_called_once_with(0)

	def test_get_audio(self):
		self.pipeline.amix.getAudioSource.return_value = 0
		self.assertResponds(b'get_audio\n',
				    b'audio_status cam1\n')

	def test_set_audio(self):
		self.pipeline.amix.getAudioSource.return_value = 1
		self.assertNotifies(b'set_audio cam2\n',
				    b'audio_status cam2\n')
		self.pipeline.amix.setAudioSource.assert_called_once_with(1)

	def test_get_composite_mode(self):
		self.pipeline.vmix.getCompositeMode.return_value = CompositeModes.picture_in_picture
		self.assertResponds(b'get_composite_mode\n',
				    b'composite_mode picture_in_picture\n')

	def test_set_composite_mode(self):
		self.pipeline.vmix.getCompositeMode.return_value = CompositeModes.picture_in_picture
		self.assertNotifies(b'set_composite_mode picture_in_picture\n',
				    b'composite_mode picture_in_picture\n')
		self.pipeline.vmix.setCompositeMode.assert_called_once_with(CompositeModes.picture_in_picture)

	def test_set_videos_and_composite(self):
		self.pipeline.vmix.getVideoSourceA.return_value = 1
		self.pipeline.vmix.getVideoSourceB.return_value = 0
		self.pipeline.vmix.getCompositeMode.return_value = CompositeModes.picture_in_picture
		self.assertNotifies(b'set_videos_and_composite cam2 cam1 picture_in_picture\n',
				    b'composite_mode picture_in_picture\n' +
				    b'video_status cam2 cam1\n')
		self.pipeline.vmix.setVideoSourceA.assert_called_once_with(1)
		self.pipeline.vmix.setVideoSourceB.assert_called_once_with(0)
		self.pipeline.vmix.setCompositeMode.assert_called_once_with(CompositeModes.picture_in_picture)

	def test_get_stream_status(self):
		self.pipeline.streamblanker.blankSource = None
		self.assertResponds(b'get_stream_status\n',
				    b'stream_status live\n')

		self.pipeline.streamblanker.blankSource = 0
		self.assertResponds(b'get_stream_status\n',
				    b'stream_status blank pause\n')

	def test_set_stream_blank(self):
		self.pipeline.streamblanker.blankSource = 0
		self.assertNotifies(b'set_stream_blank pause\n',
				    b'stream_status blank pause\n')
		self.pipeline.streamblanker.setBlankSource.assert_called_once_with(0)

	def test_set_stream_live(self):
		self.pipeline.streamblanker.blankSource = None
		self.assertNotifies(b'set_stream_live\n',
				    b'stream_status live\n')
		self.pipeline.streamblanker.setBlankSource.assert_called_once_with(None)

	def test_get_config(self):
		tr, proto = self.makeConnection()
		proto.dataReceived(b'get_config\n')
		self.assertRegex(tr.value(), b'server_config .*\n')
