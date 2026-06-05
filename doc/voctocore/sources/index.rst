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

``volume``
   Audio volume for this source, between ``0.0`` and ``1.0``.
   Default: ``0.0``.
