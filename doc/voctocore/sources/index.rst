Sources
=======

A *source* is an audio/video input to voctocore. All sources must be listed
in ``mix/sources``:

.. code-block:: ini

   [mix]
   sources = cam1,cam2,laptop

Each source name must be unique. The ``kind`` attribute in the source's own
section selects the input type. Without a ``kind``, the source defaults to a
:doc:`test source <test>`.

.. code-block:: ini

   [source.cam1]
   kind = tcp

   [source.cam2]
   kind = decklink
   devicenumber = 1

.. toctree::
   :caption: Source types

   test
   tcp
   file
   decklink
   aja
   img
   v4l2
   rpicam
   pa
   alsa
   gs

.. toctree::
   :caption: Special sources

   background
   blinder
   overlay
   live

.. _common-source-attributes:

Common source attributes
------------------------

These attributes apply to all source kinds.

``scan``
   Video scan mode. Default: ``progressive``.

   Accepted values: ``progressive``, ``interlaced``, ``psf``
   (Progressive Segmented Frame).

``audio.<streamname>``
   Defines a named audio stream from the source's input channels. The value
   is a plus-separated list of 0-based channel indices on the source.

   Example — expose the source's first two input channels as a stereo
   stream named ``music``::

      [source.cam1]
      kind = decklink
      audio.music = 0+1

   A source can declare multiple ``audio.*`` streams (e.g. ``audio.speech =
   2``). If no ``audio.*`` option is set, the source contributes no audio
   to the mix.

``volume``
   Initial audio volume for the source. Currently only read for
   ``[source.blinder]`` — setting it on other sources has no effect.
   Default: ``1.0``.
