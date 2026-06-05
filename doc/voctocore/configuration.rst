Configuration Reference
=======================

voctocore reads an INI-style configuration file. The search order is:

1. Path given by ``-i`` on the command line
2. ``~/.config/voctomix/voctocore.ini``
3. ``/etc/voctomix/voctocore.ini``
4. ``voctocore/default-config.ini`` (repository default)

``[mix]`` — core mixing settings
---------------------------------

``sources``
   Comma-separated list of source names. **Required.**
   Example: ``cam1,cam2,laptop``

``livesources``
   Sources to expose as additional live outputs. Example: ``grabber``

``backgrounds``
   Background source names, enables multi-background mode.
   Example: ``bg_fs,bg_sbs``

``videocaps``
   GStreamer caps string for the video format of the mix.
   Default: ``video/x-raw,format=I420,width=1920,height=1080,framerate=25/1,pixel-aspect-ratio=1/1``

``audiocaps``
   GStreamer caps string for the audio format of the mix.
   Default: ``audio/x-raw,format=S16LE,channels=2,layout=interleaved,rate=48000``

``nosignal``
   Test pattern shown when a source has no signal. Default: ``smpte100``.
   Set to ``none`` to disable the no-signal fallback.

``audiomixmatrix``
   Controls how input audio channels are mapped to output audio channels
   before the mix is sent downstream. Each value is a floating-point gain
   (``0.0`` = silent, ``1.0`` = full volume).

   Format: space-separated values within a row, rows separated by ``/``::

      <out0_from_in0> <out0_from_in1> ... / <out1_from_in0> <out1_from_in1> ...

   * The number of **columns** equals the number of input channels.
   * The number of **rows** equals the number of output channels.
   * Each cell ``[row][col]`` sets how much of input channel *col* is mixed
     into output channel *row*.

   Default: identity matrix derived from the ``channels`` value in
   ``audiocaps`` (pass-through, no remixing).

   **Examples** (for a standard 2-channel stereo stream):

   Pass-through — left stays left, right stays right::

      audiomixmatrix = 1 0 / 0 1

   Swap left and right channels::

      audiomixmatrix = 0 1 / 1 0

   Downmix stereo to mono (average both channels into a single output)::

      audiomixmatrix = 0.5 0.5

   Duplicate a mono source to both stereo outputs::

      audiomixmatrix = 1 / 1

   Send only the left input channel to both outputs (useful when a source
   carries audio only on one channel)::

      audiomixmatrix = 1 0 / 1 0

``[source.<name>]`` — per-source settings
------------------------------------------

Each source defined in ``mix/sources`` can have its own section. See
:doc:`sources/index` for the full per-kind option reference.

``[composites]`` — video composites
------------------------------------

Composites define how sources A and B are positioned in the output frame.
Each line defines one composite:

.. code-block:: ini

   [composites]
   fullscreen.alpha-b = 0
   sidebyside.a = 0/0/960/1080
   sidebyside.b = 960/0/1920/1080
   pip.a = 0/0/1920/1080
   pip.b = 1440/810/1920/1080

See :doc:`../transitions` for the full composite and transition syntax.

``[transitions]`` — animated transitions
-----------------------------------------

.. code-block:: ini

   [transitions]
   FADE = 750, fullscreen / fullscreen

Format: ``<name> = <duration_ms>, <from_composite> / [intermediate /] <to_composite>``

See :doc:`../transitions` for details.

``[previews]`` — preview output
--------------------------------

``enabled``
   Enable encoded preview outputs for the GUI. Default: ``false``.

``live``
   Which live sources to include in the preview output. Default: ``false``.
   Accepted values: ``true`` (mix only), ``all``, or a comma-separated list
   of source names from ``mix/livesources``.

``width``
   Preview frame width in pixels. Default: ``320``.

``height``
   Preview frame height in pixels. Default: width × 9/16.

``nameoverlay``
   Overlay the source name on preview thumbnails. Default: ``true``.

``vaapi``
   Use VAAPI hardware encoder for previews. Omit to use CPU encoding.
   Accepted values: ``h264``, ``mpeg2``, ``jpeg``

``scale-method``
   Scaling quality. Default: ``0``.

   - ``0`` — default
   - ``1`` — fast, lower quality
   - ``2`` — high quality, slower

``vaapi-denoise``
   Apply VAAPI denoising before encoding. Default: ``false``.


``[blinder]`` — stream blanker
-------------------------------

See :doc:`sources/blinder`.

``[overlay]`` — image overlays
-------------------------------

See :doc:`sources/overlay`.

``[avrawoutput]`` — raw A/V output
-----------------------------------

``enabled``
   Expose the full-quality mix as a raw Matroska stream on port ``11000``.
   Default: ``true`` (enabled unless explicitly set to ``false``).

``[mirrors]`` — source mirror ports
-------------------------------------

``enabled``
   Expose a copy of each source's raw input stream on its own TCP port.
   Default: ``false``.

``[localrecording]`` — local recording
---------------------------------------

.. note::
   Local recording is not yet implemented in voctomix 2.0.

``enabled``
   Enable local recording output. Default: ``false``.

``[programoutput]`` — direct monitor output
--------------------------------------------

Outputs the mix recording directly to a GStreamer video/audio sink (e.g. a
display or an AJA output card).

``enabled``
   Enable the program output. Default: ``false``.

``videosink``
   GStreamer element or pipeline fragment for video output.
   Default: ``autovideosink``

``audiosink``
   GStreamer element or pipeline fragment for audio output.
   Default: ``autoaudiosink``

``[output-buffers]`` — output queue sizes
------------------------------------------

Fine-tune the output buffer depth per channel (in frames):

.. code-block:: ini

   [output-buffers]
   mix = 500
   cam1 = 500

Default is ``500`` for all channels.

