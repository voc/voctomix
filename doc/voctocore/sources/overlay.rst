Overlay sources
===============

Overlays are PNG images composited on top (highest z-order) of the mix,
typically used for lower thirds. Configure the image directory with
``overlay/path``:

.. code-block:: ini

   [overlay]
   path = ./data/overlays

Single overlay file
-------------------

The simplest option: set one overlay that is active at startup.

.. code-block:: ini

   [overlay]
   file = watermark.png|Watermark

The part after ``|`` is a human-readable label shown in the UI.

Multiple overlay files
----------------------

A comma-separated list of images the operator can switch between:

.. code-block:: ini

   [overlay]
   files = first.png|1st overlay, second.png|2nd overlay, third.png|3rd overlay

No overlay is active at startup when using ``files``.

Schedule-driven overlays
------------------------

Provide a `Frab/Pretalx JSON schedule <https://github.com/voc/voctosched>`_
and voctocore auto-generates overlay file names per speaker:

.. code-block:: ini

   [overlay]
   schedule = schedule.json
   room = HALL 1

voctocore looks for files named ``event_{eid}_person_{pid}.png`` (individual
speaker) and ``event_{eid}_persons.png`` (all speakers) in the overlay path.
Only files that actually exist on disk are offered as options.

Filter by room to restrict overlays to the current hall. Use ``event`` instead
of ``room`` to pin to a specific event ID regardless of time:

.. code-block:: ini

   [overlay]
   schedule = schedule.json
   event = 42

Additional options
------------------

``auto-off``
   Automatically remove the overlay when the composite changes.
   Default: ``true``.

``user-auto-off``
   Expose the auto-off toggle in the voctogui toolbar.
   Default: ``false``.

``blend``
   Overlay fade-in/out duration in milliseconds. Default: ``300``.
