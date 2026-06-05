Test sources
============

``kind = test`` (or omit ``kind``) — generates video and audio test signals
using GStreamer's ``videotestsrc`` and ``audiotestsrc``.

When multiple test sources exist, their patterns cycle through the available
values in order of appearance in ``mix/sources``.

Configuration options
---------------------

``pattern``
   Video test pattern. Default: auto-cycled through sources in order.

   Available values: ``smpte``, ``ball``, ``red``, ``green``, ``blue``,
   ``black``, ``white``, ``checkers-1``, ``checkers-2``, ``checkers-4``,
   ``checkers-8``, ``circular``, ``blink``, ``smpte75``, ``zone-plate``,
   ``gamut``, ``chroma-zone-plate``, ``solid-color``, ``smpte100``, ``bar``,
   ``snow``, ``pinwheel``, ``spokes``, ``gradient``, ``colors``

``wave``
   Audio test waveform. Default: ``sine``.

   Available values: ``sine``, ``square``, ``saw``, ``triangle``,
   ``silence``, ``white-noise``, ``pink-noise``, ``sine-table``, ``ticks``,
   ``gaussian-noise``, ``red-noise``, ``blue-noise``, ``violet-noise``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,cam2

   [source.cam1]
   kind = test
   pattern = ball
   wave = white-noise
