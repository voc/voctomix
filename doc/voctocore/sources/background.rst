Background source
=================

The background source is placed at the bottom of the video compositor
(z-order 0) and is **not** listed in ``mix/sources``. By default it produces
a black test pattern.

.. code-block:: ini

   [source.background]
   kind = img
   file = bg.png

The background source accepts any source kind. It is video only — audio is
ignored.

Multiple backgrounds
--------------------

You can assign different backgrounds to different composites using
``mix/backgrounds``. The default ``background`` source is not used when this
is set.

.. code-block:: ini

   [mix]
   backgrounds = background_fs,background_sbs

   [source.background_fs]
   kind = img
   file = bg_fullscreen.png
   composites = fullscreen

   [source.background_sbs]
   kind = test
   pattern = black
   composites = sidebyside,pip

When a composite switch occurs, voctocore cuts or fades to the matching
background automatically. The first background in the list is used as
fallback when no ``composites`` match.
