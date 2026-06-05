File sources
============

``kind = file`` — plays a local file in a loop (e.g. a pause animation).

Currently expects MPEG-TS containers with MPEG-2 video and MP2/MP3 audio.

Configuration options
---------------------

``location``
   Path to the media file. **Required.**

``loop``
   Whether to loop the file. Default: ``true``.

Example
-------

.. code-block:: ini

   [source.blinder]
   kind = file
   location = /path/to/pause.ts
   loop = true
