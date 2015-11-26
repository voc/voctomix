#!/usr/bin/python3
import logging

class LogFormatter(logging.Formatter):
	def __init__(self, docolor):
		super().__init__()
		self.docolor = docolor

	def formatMessage(self, record):
		if self.docolor:
			c_lvl = 33
			c_mod = 32
			c_msg = 0

			if record.levelno == logging.WARNING:
				c_lvl = 31
				#c_mod = 33
				c_msg = 33

			elif record.levelno > logging.WARNING:
				c_lvl = 31
				c_mod = 31
				c_msg = 31

			fmt = '\x1b['+str(c_lvl)+'m%(levelname)8s\x1b[0m \x1b['+str(c_mod)+'m%(name)s\x1b['+str(c_msg)+'m: %(message)s\x1b[0m'
		else:
			fmt = '%(levelname)8s %(name)s: %(message)s'

		return fmt % record.__dict__


class LogHandler(logging.StreamHandler):
	def __init__(self, docolor):
		super().__init__()
		self.setFormatter(LogFormatter(docolor))
