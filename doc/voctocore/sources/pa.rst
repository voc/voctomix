PulseAudio sources
==================

``kind = pa`` — captures audio from a PulseAudio device. This source is
audio-only; pair it with a video-only source such as :doc:`v4l2` or
:doc:`rpicam` when you need both.

Configuration options
---------------------

``device``
   PulseAudio source or monitor name. Default: ``auto``.

   Use ``pactl list sources short`` to list available devices. Monitor
   sources (e.g. ``alsa_output.*.monitor``) can be used to capture the
   output of a playback device.

   Example: ``alsa_output.usb-Logitech_Headset-00.analog-stereo.monitor``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,headset

   [source.headset]
   kind = pa
   device = alsa_output.usb-Logitech_Headset-00.analog-stereo.monitor

.. seealso::
   :ref:`common-source-attributes` for the ``scan`` and ``volume`` attributes that apply to all source kinds.
