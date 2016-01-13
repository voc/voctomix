#!/usr/bin/python3
import logging, time

class LogFormatter(logging.Formatter):
	def __init__(self, docolor, timestamps=False):
		super().__init__()
		self.docolor = docolor
		self.timestamps = timestamps

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
			if self.timestamps:
				fmt = '%(asctime)s \x1b['+str(c_lvl)+'m%(levelname)8s\x1b[0m \x1b['+str(c_mod)+'m%(name)s\x1b['+str(c_msg)+'m: %(message)s\x1b[0m'
			else:
				fmt = '\x1b['+str(c_lvl)+'m%(levelname)8s\x1b[0m \x1b['+str(c_mod)+'m%(name)s\x1b['+str(c_msg)+'m: %(message)s\x1b[0m'
		else:
			if self.timestamps:
				fmt = '%(asctime)s %(levelname)8s %(name)s: %(message)s'
			else:
				fmt = '%(levelname)8s %(name)s: %(message)s'

		if not 'asctime' in record.__dict__:
			record.__dict__['asctime']=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(record.__dict__['created']))
		return fmt % record.__dict__


class LogHandler(logging.StreamHandler):
	def __init__(self, docolor, timestamps):
		super().__init__()
		self.setFormatter(LogFormatter(docolor,timestamps))
