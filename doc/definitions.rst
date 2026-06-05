Namings and Definitions
=======================

.. Please try to keep this file sorted alphabetically.

blinder
-------

The blinder (formerly called "stream blanker") suppresses all live outputs
while keeping the mix recording running.
It is used between talks or during breaks so that the audience sees a pause
screen while the recording crew can still work.

.. _composite:

composite
---------

A composite is a combination of up to two video :ref:`sources <sources>`
laid out together into one output frame. Built-in composites include
fullscreen, picture-in-picture (pip), side-by-side (sbs) and
side-by-side-preview (sbsp). Custom composites can be defined in the
configuration. See :doc:`transitions` for details.

.. _sources:

sources
-------

A source is an audio/video input connected to :ref:`voctocore <voctocore>`.
Sources can be physical captures (e.g. a camera or slide grabber via
TCP/Decklink/AJA/V4L2) or generated signals (test patterns, image files,
looping video files).

All sources are listed in ``mix/sources`` in the configuration.

transition
----------

A transition is an animated fade between two :ref:`composites <composite>`.
voctomix interpolates key frames using B-Splines to produce smooth motion.
See :doc:`transitions` for the full reference.

.. _voctocore:

voctocore
---------

voctocore is the mixing engine. It runs a GStreamer pipeline and listens
on port ``9999`` for control connections. All :ref:`sources` connect to it.
:ref:`voctogui` connects to it over the network to send commands and receive
preview streams.

See :doc:`voctocore/index` for details.

.. _voctogui:

voctogui
--------

voctogui is the graphical control interface for :ref:`voctocore`.
It connects over TCP, displays previews of all sources and the mix, and
provides toolbars for all mixing operations.

See :doc:`voctogui/index` for details.
