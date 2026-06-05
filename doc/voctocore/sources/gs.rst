GStreamer pipe sources
======================

``kind = gs`` — builds a custom A/V source from raw GStreamer pipeline
fragments. Use this when none of the built-in source types fits your hardware.

Configuration options
---------------------

``video_source``
   GStreamer pipeline fragment for video.
   Default: ``videotestsrc pattern=ball motion=hsweep animation-mode=wall-time``

``audio_source``
   GStreamer pipeline fragment for audio.
   Default: ``audiotestsrc wave=ticks freq=330``

``video_debug``
   Add debug overlays to the video stream. Default: ``false``.

``audio_debug``
   Add debug info to the audio stream. Default: ``false``.

Example
-------

.. code-block:: ini

   [source.cam1]
   kind = gs
   video_source = v4l2src device=/dev/video0 ! image/jpeg,width=1920,height=1080 ! jpegdec
   audio_source = pulsesrc device=alsa_input.usb-device
