Running voctocore
=================

Synopsis
--------

.. code-block:: text

   python3 -m voctocore [-h] [-v] [-c {auto,always,never}] [-t]
                        [-i INI_FILE] [-p] [-n] [-d] [-D GST_DEBUG_DETAILS]
                        [-g]

Description
-----------

voctocore is the mixing engine of voctomix, a software video switcher for
live event streaming. It accepts video and audio streams from multiple sources
over TCP, composites them into a mix, and exposes the result for recording and
streaming.

voctocore is configured via an INI file and exposes a control API on TCP
port 9999. The graphical operator interface is provided by voctogui(1).

Options
-------

.. option:: -h, --help

   Show help message and exit.

.. option:: -v, --verbose

   Increase log verbosity. Use ``-v``, ``-vv``, or ``-vvv`` for more detail.

.. option:: -c {auto,always,never}, --color {auto,always,never}

   Control ANSI colour in log output. Default: ``auto``.

.. option:: -t, --timestamp

   Add timestamps to log output.

.. option:: -i INI_FILE, --ini-file INI_FILE

   Load a custom configuration file.

.. option:: -p, --pipeline

   Write GStreamer pipeline descriptions to text files instead of starting
   the mixer.

.. option:: -n, --no-bins

   Do not wrap pipeline sections in GStreamer bins. Useful for debugging
   pipeline graphs.

.. option:: -d, --dot

   Write DOT graph files of the GStreamer pipeline into the directory set by
   ``$GST_DEBUG_DUMP_DOT_DIR``.

.. option:: -D GST_DEBUG_DETAILS, --gst-debug-details GST_DEBUG_DETAILS

   Like ``-d`` but control the detail level of the DOT graph (bitmask,
   default ``1``): 1 caps names, 2 caps details, 4 modified parameters,
   8 element states, 16 full parameter values.

.. option:: -g, --gstreamer-log

   Include GStreamer messages in the log. Use ``-g``, ``-gg``, or ``-ggg``
   for increasing GStreamer verbosity.

Files
-----

``~/.config/voctomix/voctocore.ini``
   Per-user configuration file.

``/etc/voctomix/voctocore.ini``
   System-wide configuration file.

``voctocore/default-config.ini``
   Repository default configuration.

See Also
--------

voctogui(1)
