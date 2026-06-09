voctogui Configuration Reference
==================================

voctogui reads an INI configuration file (default:
``voctogui/default-config.ini``). The server's configuration is merged in
at startup, so most options only need to be set in the voctocore config.

``[server]`` — connection
--------------------------

``host``
   Hostname or IP of the voctocore instance. **Required.**
   Example: ``localhost``, ``192.168.1.10``

``[mainwindow]`` — window properties
--------------------------------------

``width``
   Window width in pixels when not in fullscreen. Default: automatic.

``height``
   Window height in pixels when not in fullscreen. Default: automatic.

``forcefullscreen``
   Start in fullscreen mode. Default: ``false``.

``[toolbar]`` — main toolbar buttons
--------------------------------------

``close``
   Show the close button. Default: ``true``.

``fullscreen``
   Show the fullscreen toggle button. Default: ``false``.

``queues``
   Show the queue depth panel toggle button. Default: ``false``.

``ports``
   Show the port status panel toggle button. Default: ``false``.

``presets``
   Comma-separated list of preset names (see :ref:`presets <preset-buttons>` below).
   Default: empty (the preset toolbar is hidden).

.. note::
   To prevent users from enabling these features via a local GUI config,
   set them to ``false`` in the voctocore config (which takes precedence).

``[toolbar.sources.a]`` and ``[toolbar.sources.b]`` — source buttons
----------------------------------------------------------------------

Without explicit configuration, source buttons are auto-generated from
``mix/sources`` with uppercase labels and keyboard shortcuts ``F1``–``F4``
(A) and ``1``–``4`` (B).

.. code-block:: ini

   [toolbar.sources.a]
   buttons = cam,grabber

   cam.name = CAMERA
   cam.tip  = Select camera on A

   grabber.name = LAPTOP
   grabber.tip  = Select speaker's laptop on A

   [toolbar.sources.b]
   cam.name    = CAMERA
   grabber.name = LAPTOP

The ``buttons`` key lists which sources appear as buttons (comma-separated
source names from ``mix/sources``). Each button supports the
:ref:`common button attributes <common-button-attrs>`.

``[toolbar.composites]`` — composite buttons
----------------------------------------------

Without configuration, composite buttons are auto-generated with uppercase
labels and keyboard shortcuts ``F5``–``F8``.

.. code-block:: ini

   [toolbar.composites]
   buttons = fullscreen,sidebyside

   fullscreen.name = FULL SCREEN
   fullscreen.tip  = Show channel A full screen

   sidebyside.name = SIDE BY SIDE
   sidebyside.tip  = Put channel A beside channel B

``[toolbar.mods]`` — modifier buttons
---------------------------------------

Modifier buttons apply a string replacement to the current composite name,
allowing mirroring or aspect-ratio variants without separate composites.
Default keyboard shortcuts are ``F9``–``F12``.

.. code-block:: ini

   [toolbar.mods]
   buttons = mirror,ratio43

   mirror.name    = MIRROR
   mirror.replace = lecture->|lecture

   ratio43.name    = 4:3
   ratio43.replace = lecture->lecture_43

Each button's ``replace`` attribute is a substitution rule of the form
``original->replacement``. Prefixing a composite name with ``|`` mirrors
all coordinates.

``[toolbar.mix]`` — mix action buttons
----------------------------------------

Controls which mix actions are shown. Available buttons: ``retake``,
``cut``, ``trans``. Default keyboard shortcuts: ``BackSpace`` (retake),
``Return`` (cut), ``space`` (trans).

.. code-block:: ini

   [toolbar.mix]
   buttons = cut,trans

   trans.expand = true

``[toolbar.insert]`` — overlay insertion toolbar
-------------------------------------------------

.. code-block:: ini

   [toolbar.insert]
   auto-off.key = o
   auto-off.tip = Automatically turn off insertion before every mix

   update.key   = u
   update.tip   = Update current event

   insert.key   = i
   insert.tip   = Show or hide current insertion

.. _preset-buttons:

``[preset.<name>]`` — preset buttons
--------------------------------------

Preset buttons are one-click shortcuts that switch to a specific composite
with specific sources on channels A and B. List the presets you want in
``toolbar/presets``; each preset name encodes the target state in the form
``<composite>_<sourceA>[_<sourceB>]``. If ``<sourceB>`` is omitted, voctogui
picks the first available source other than ``<sourceA>``.

Each preset can be customised with a ``[preset.<name>]`` section. Unlike
other toolbar sections, attributes here are written without a button-name
prefix because each preset has its own section:

.. code-block:: ini

   [toolbar]
   presets = fs_cam1, fs_cam2, sbs_cam1_cam2, pip_cam1_cam2

   [preset.fs_cam1]
   name = CAM 1
   key  = 1
   icon = camera-video-symbolic

   [preset.fs_cam2]
   name = CAM 2
   key  = 2
   icon = camera-video-symbolic

   [preset.sbs_cam1_cam2]
   name = SIDE|BY SIDE
   key  = s

   [preset.pip_cam1_cam2]
   name = PIP
   key  = p

Preset-specific attribute:

``icon``
   File name of an icon to display on the button. Looked up relative to
   ``voctogui/ui/``. Optional.

``name`` and ``key`` work as documented under :ref:`common-button-attrs`
(``name`` accepts ``|`` to insert a line break). If no presets are listed in
``toolbar/presets`` the preset toolbar is hidden entirely.

.. _common-button-attrs:

Common button attributes
-------------------------

These attributes can be set on any button in any toolbar section.

``.name``
   Label shown on the button.

``.tip``
   Tooltip text.

``.key``
   GTK keyboard accelerator. See the
   `GTK accelerator syntax <https://developer.gnome.org/gtk3/stable/gtk3-Keyboard-Accelerators.html>`_
   for the format.

``.expand``
   Whether the button expands to fill available space. Accepts ``true`` or
   ``false``.

``.pos``
   Position (0-based integer) within the toolbar. Appended in config order
   if omitted.

``.replace``
   Composite name substitution rule (modifier buttons only).

``[videodisplay]`` — display system
-------------------------------------

``system``
   GStreamer video display system used to render preview thumbnails.
   Default: ``gl``. Accepted values: ``gl``, ``xv``, ``x``, ``vaapi``

``[audio]`` — audio playback
-----------------------------

``play``
   Play audio through the local sound system. Default: ``false``.

``volumecontrol``
   Show per-source volume sliders. Default: ``true``.

``forcevolumecontrol``
   Show volume sliders even when a fixed audio source is configured.
   Default: ``false``.

Customising the UI style
-------------------------

Edit ``voctogui/ui/voctogui.css`` to change colours, sizes, and fonts.

To discover GTK widget names and CSS classes interactively:

.. code-block:: bash

   GTK_DEBUG=interactive python3 -m voctogui
