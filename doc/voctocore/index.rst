voctocore
=========

voctocore is the mixing engine of voctomix. It runs a
`GStreamer <https://gstreamer.freedesktop.org/>`_ pipeline and exposes a
TCP control interface on port ``9999``.

Features
--------

* Matroska-enveloped A/V source input via TCP
* Image sources via URI or file path
* `Decklink <https://www.blackmagicdesign.com/products/decklink>`_ A/V capture cards
* `AJA <https://www.aja.com/family/desktop-io>`_ Desktop I/O capture cards
* Video4Linux2 video sources
* Raspberry Pi camera sources
* GStreamer test sources
* Looping file sources
* Scaling and format conversion of input sources
* Video compositing (fullscreen, picture-in-picture, side-by-side, …)
* Blinder / stream blanker for live outputs
* Low-resolution preview outputs for the GUI
* High-resolution outputs for recording
* Image overlays (lower thirds)
* Schedule-driven overlay selection
* Video transitions (animated fades between composites)
* Remote control via TCP command interface

Quick start
-----------

Start voctocore with the default configuration:

.. code-block:: bash

   python3 -m voctocore

Or with a custom config file:

.. code-block:: bash

   python3 -m voctocore -i /path/to/config.ini

See :doc:`running` for all command-line options and :doc:`configuration` for
the full configuration reference.
