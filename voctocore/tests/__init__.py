
import os
import unittest

def load_tests(loader, standard_tests, pattern):
	if pattern is None:
		pattern = 'test*.py'
	this_dir = os.path.dirname(__file__)
	package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
	standard_tests.addTests(package_tests)
	return standard_tests
