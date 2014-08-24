from gi.repository import Gst

def iteratorHelper(it):
	while True:
		result, value = it.next()
		if result == Gst.IteratorResult.DONE:
			break

		if result != Gst.IteratorResult.OK:
			raise IteratorError(result)

		yield value
