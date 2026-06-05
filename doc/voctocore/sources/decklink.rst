Decklink sources
================

``kind = decklink`` — captures A/V from a
`Blackmagic Decklink <https://www.blackmagicdesign.com/products/decklink>`_
card.

Configuration options
---------------------

``devicenumber``
   Decklink device number. Default: ``0``.

``video_connection``
   Video input connection type. Default: ``auto``.

   Accepted values: ``auto``, ``SDI``, ``HDMI``, and others supported by the
   card.

``video_mode``
   Video mode. Default: ``auto``.

   Examples: ``1080p25``, ``1080i50``, ``720p50``.

``video_format``
   Video pixel format. Default: ``auto``.

   Examples: ``8bit-YUV``, ``10bit-YUV``, ``8bit-ARGB``.

``audio_connection``
   Audio input connection type. Default: ``auto``.

   Accepted values: ``auto``, ``embedded``, ``aes``, ``analog``,
   ``analog-xlr``, ``analog-rca``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,cam2

   [source.cam1]
   kind = decklink
   devicenumber = 0

   [source.cam2]
   kind = decklink
   devicenumber = 1
   video_mode = 1080p25

.. seealso::
   :ref:`common-source-attributes` for the ``scan`` and ``volume`` attributes that apply to all source kinds.
