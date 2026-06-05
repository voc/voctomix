Raspberry Pi camera sources
============================

``kind = RPICam`` — captures video from a Raspberry Pi camera module using
the ``rpicamsrc`` GStreamer element. This source is video-only; use a separate
:doc:`pa` or :doc:`alsa` source for audio.

Configuration options
---------------------

``device``
   Camera device node. Default: ``/dev/video0``.

``width``
   Capture width in pixels. Default: ``1920``.

``height``
   Capture height in pixels. Default: ``1080``.

``format``
   Pixel format. Default: ``YUY2``.

``framerate``
   Capture frame rate as numerator/denominator. Default: ``25/1``.

``type``
   GStreamer media type string. Default: ``video/x-raw``.

``crop``
   Crop the captured frame, given as four space-separated pixel values:
   ``bottom left right top``. Omit to disable cropping.

   Example: ``crop = 8 0 0 0`` removes 8 pixels from the bottom.

``annotation``
   Enable camera annotation mode (e.g. burn-in timestamp).
   Passed directly to the ``annotation-mode`` property of ``rpicamsrc``.
   Example: ``annotation = time``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1

   [source.cam1]
   kind = RPICam
   width = 1920
   height = 1088
   crop = 8 0 0 0
   framerate = 25/1
   format = I420
   type = video/x-raw
   annotation = time
