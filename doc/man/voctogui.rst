Running voctogui
================

Synopsis
--------

.. code-block:: text

   python3 -m voctogui [-h] [-v] [-c {auto,always,never}] [-t]
                       [-i INI_FILE] [-H HOST] [-d] [-D DETAILS] [-g]

Description
-----------

voctogui is the graphical control interface for voctocore(1). It connects to
a running voctocore instance over TCP and provides live source previews,
source selection, composite and transition controls, blinder toggle, and
overlay insertion.

Configuration is read from an INI file. When voctogui connects to voctocore
the server's configuration is merged in, so most options only need to be set
once in the voctocore config.

Options
-------

.. option:: -h, --help

   Show help and exit.

.. option:: -v, --verbose

   Increase log verbosity (``-v``, ``-vv``, ``-vvv``).

.. option:: -c {auto,always,never}, --color {auto,always,never}

   ANSI colour in log output. Default: ``auto``.

.. option:: -t, --timestamp

   Add timestamps to log output.

.. option:: -i INI_FILE, --ini-file INI_FILE

   Load a custom configuration file.
   Default: ``voctogui/default-config.ini``.

.. option:: -H HOST, --host HOST

   Connect to this voctocore host instead of the one in the config file.

.. option:: -d, --dot

   Write DOT graphs of GStreamer pipelines into ``$GST_DEBUG_DUMP_DOT_DIR``.

.. option:: -D DETAILS, --gst-debug-details DETAILS

   Like ``-d`` but set the DOT detail level (bitmask, default ``15``).

.. option:: -g, --gstreamer-log

   Include GStreamer messages in the log (``-g``, ``-gg``, ``-ggg``).

Files
-----

``~/.config/voctomix/voctogui.ini``
   Per-user configuration file.

``/etc/voctomix/voctogui.ini``
   System-wide configuration file.

``voctogui/default-config.ini``
   Repository default configuration.

See Also
--------

voctocore(1)
