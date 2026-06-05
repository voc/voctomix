Example Scripts
================

The ``example-scripts/`` directory contains tools that show how to connect
different A/V sources and sinks to voctocore. Some can be used in production
as-is; others serve as starting templates.

The c3voc primarily uses the **ffmpeg**-based scripts, which are tested in
production and are the preferred method for getting data in and out of
voctomix.

voctoremote
-----------

``example-scripts/voctoremote/`` — a simple web interface with configurable
buttons that send commands to the voctocore control server (port ``9999``).
Useful as a remote control for the ISDN project or operator tablet.

Requirements: Python 3 and Flask.

.. code-block:: bash

   cd example-scripts/voctoremote
   pip install -r requirements.txt
   ./voctoremote.py

For production deployment use NginX + Gunicorn.

voctomidi
---------

``example-scripts/voctomidi/`` — maps MIDI NOTE ON events from a MIDI
controller to voctocore layouts.

Configuration (``default-config.ini``):

.. code-block:: ini

   [midi]
   ; device name or port; leave unset to get a list of available devices
   device = LPD8

   [eventmap]
   ; <note> = <srcA> <srcB> <composite>
   36 = cam1 cam2 fullscreen
   37 = cam2 cam1 fullscreen
   38 = cam1 cam2 sidebyside

An example config for the `AKAI Professional LPD-8
<http://www.akaipro.com/products/pad-controllers/lpd-8>`_ is included as
``lpd8-config.ini``.

voctolight
----------

``example-scripts/voctolight/`` — controls tally lights or external
indicators based on the current voctocore mixing state.

voctoremote
-----------

``example-scripts/voctoremote/`` — a simple Flask web app that sends
voctocore commands when buttons are clicked. Suitable for a tablet-based
operator remote.

.. code-block:: bash

   cd example-scripts/voctoremote
   pip install -r requirements.txt
   ./voctoremote.py

voctopanel
----------

``example-scripts/voctopanel/`` — a minimal control panel for voctocore.

Default config: ``example-scripts/voctopanel/default-config.ini``.

ffmpeg sources and sinks
------------------------

``example-scripts/`` contains several ffmpeg-based helper scripts for
common capture and output tasks. These are the production-tested scripts
used by c3voc.

Use the ``default-config.sh`` as a starting point:

.. code-block:: bash

   source example-scripts/default-config.sh
