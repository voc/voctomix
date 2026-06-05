voctogui
========

voctogui is the graphical control interface for :doc:`../voctocore/index`.
It connects to a running voctocore instance over TCP and provides:

* Live previews of all sources and the mix
* Source selection buttons for channels A and B
* Composite and transition controls
* Blinder (stream blanker) toggle
* Overlay / lower-third insertion controls
* Expert views: port status, queue depths

.. image:: ../../voctogui/doc/images/voc2gui.png
   :alt: voctogui screenshot
   :align: center

Running
-------

.. code-block:: text

   python3 -m voctogui [-h] [-v] [-c {auto,always,never}] [-t]
                       [-i INI_FILE] [-H HOST] [-d] [-D DETAILS] [-g]

Command-line options
````````````````````

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

   Connect to this host instead of the one in the config file.

.. option:: -d, --dot

   Write DOT graphs of GStreamer pipelines into ``$GST_DEBUG_DUMP_DOT_DIR``.

.. option:: -D DETAILS, --gst-debug-details DETAILS

   Like ``-d`` but set the DOT detail level (bitmask, default ``15``).

.. option:: -g, --gstreamer-log

   Include GStreamer messages in the voctogui log (``-g``, ``-gg``, ``-ggg``).

Server configuration takes precedence
--------------------------------------

When voctogui connects to voctocore, the server's configuration is merged
into the client's. All options except ``server/host`` can be defined in the
voctocore config and will be used by all connecting GUI instances automatically.
This means you generally only need ``server/host`` in the GUI config file.

See :doc:`configuration` for the full option reference.
