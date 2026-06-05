Running voctocore
=================

.. code-block:: text

   python3 -m voctocore [-h] [-v] [-c {auto,always,never}] [-t]
                        [-i INI_FILE] [-p] [-n] [-d] [-D GST_DEBUG_DETAILS]
                        [-g]

Command-line options
--------------------

.. option:: -h, --help

   Show help message and exit.

.. option:: -v, --verbose

   Increase log verbosity. Use ``-v``, ``-vv``, or ``-vvv`` for more detail.

.. option:: -c {auto,always,never}, --color {auto,always,never}

   Control ANSI colour in log output. Default: ``auto``.

.. option:: -t, --timestamp

   Add timestamps to log output.

.. option:: -i INI_FILE, --ini-file INI_FILE

   Load a custom configuration file. Without this option voctocore looks for
   a config file in the following order:

   1. ``~/.config/voctomix/voctocore.ini``
   2. ``/etc/voctomix/voctocore.ini``
   3. ``voctocore/default-config.ini`` (repository default)

.. option:: -p, --pipeline

   Write GStreamer pipeline descriptions to text files (one per pipeline)
   instead of starting the mixer.

.. option:: -n, --no-bins

   Do not wrap pipeline sections in GStreamer bins. Useful for debugging
   pipeline graphs where bins obscure the internal structure.

.. option:: -d, --dot

   Write DOT graph files of the GStreamer pipeline into the directory set by
   the environment variable ``GST_DEBUG_DUMP_DOT_DIR``. View them with
   `xdot <https://github.com/jrfonseca/xdot.py>`_.

.. option:: -D GST_DEBUG_DETAILS, --gst-debug-details GST_DEBUG_DETAILS

   Like ``-d`` but control the detail level of the DOT graph. The value is a
   bitmask:

   ===== =====
   Value Meaning
   ===== =====
   1     Show caps name on edges
   2     Show caps details on edges
   4     Show modified parameters on elements
   8     Show element states
   16    Show full element parameter values
   ===== =====

   Default: ``1``.

.. option:: -g, --gstreamer-log

   Include GStreamer messages in the voctocore log. Use ``-g``, ``-gg``, or
   ``-ggg`` for increasing GStreamer verbosity.
