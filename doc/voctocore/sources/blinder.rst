Blinder sources
===============

The blinder (formerly "stream blanker") suppresses all live outputs while
keeping the mix recording running. Enable it in the ``[blinder]`` section:

.. code-block:: ini

   [blinder]
   enabled = true

By default the blinder generates a SMPTE test pattern with silence. Customise
it with a ``[source.blinder]`` section using any source kind:

.. code-block:: ini

   [blinder]
   enabled = true

   [source.blinder]
   kind = test
   pattern = black
   volume = 0.0

Multiple video sources
----------------------

You can have several selectable video blinder sources (e.g. "break",
"closed") that share one audio source:

.. code-block:: ini

   [blinder]
   enabled = true
   videos = break,closed

   [source.blinder]
   kind = tcp

   [source.break]
   kind = tcp

   [source.closed]
   kind = tcp

The three sources each listen on their own TCP port (assigned sequentially
from the blinder port range). voctogui shows a button for each video source
so the operator can select which one to display.
