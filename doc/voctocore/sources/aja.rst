AJA sources
===========

``kind = aja`` — captures A/V from an
`AJA Desktop I/O <https://www.aja.com/family/desktop-io>`_ card.

The ``device`` attribute is required and is typically a truncated part of the
card's serial number. Set ``device = ?`` to print discovered cards at startup
and then exit.

Configuration options
---------------------

``device``
   AJA device identifier. **Required.** Example: ``00A00012``.

``channel``
   Input channel number. Default: ``0``. Channel 0 maps to SDI input 1,
   channel 1 to SDI input 2, and so on.

``video_mode``
   Video format. Default: ``auto``.

   Examples: ``1080p-2500``, ``1080i-5000``, ``720p-5000``.

``audio_source``
   Audio input source. Default: ``embedded``.

   Accepted values: ``embedded``, ``aes``, ``analog``, ``hdmi``, ``mic``

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,cam2

   [source.cam1]
   kind = aja
   device = 00A00012
   channel = 0

   [source.cam2]
   kind = aja
   device = 00A00012
   channel = 1

.. seealso::
   :ref:`common-source-attributes` for the ``scan`` and ``volume`` attributes that apply to all source kinds.
