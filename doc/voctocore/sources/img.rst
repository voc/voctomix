Image sources
=============

``kind = img`` — displays a still image as a video source (video only, no
audio).

Provide either ``imguri`` (any URI) or ``file`` (local path).

Configuration options
---------------------

``imguri``
   Image URI, e.g. ``http://example.com/slide.jpg``. Use instead of ``file``.

``file``
   Local image path, e.g. ``/opt/voctomix/bg.png``. Use instead of ``imguri``.

Example
-------

.. code-block:: ini

   [source.background]
   kind = img
   file = /opt/voctomix/background.png
