#!/usr/bin/python3
import logging
from gi.repository import Gst
from enum import Enum

from lib.config import Config

class AudioMix(object):
	log = logging.getLogger('VideoMix')

	mixingPipeline = None

	caps = None
	names = []

	selectedSource = 0

	def __init__(self):
		pass
