ALSA sources
============

``kind = alsa`` — captures audio from an ALSA device. This source is
audio-only; pair it with a video-only source such as :doc:`v4l2` or
:doc:`rpicam` when you need both.

Configuration options
---------------------

``device``
   ALSA device name. Default: ``hw:0``.

   Use ``aplay -l`` to list available cards and devices.

   Example: ``hw:1,0``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,mic

   [source.mic]
   kind = alsa
   device = hw:1,0
