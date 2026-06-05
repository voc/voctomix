TCP sources
===========

``kind = tcp`` — accepts Matroska-enveloped A/V streams over TCP.

TCP sources are assigned sequential ports starting from ``10000`` in the order
they appear in ``mix/sources``. The first TCP source listens on ``10000``, the
second on ``10001``, and so on.

Example
-------

.. code-block:: ini

   [mix]
   sources = cam1,cam2

   [source.cam1]
   kind = tcp

   [source.cam2]
   kind = tcp

This makes voctocore listen on port ``10000`` for ``cam1`` and ``10001`` for
``cam2``.

Sending a stream
----------------

Use ffmpeg to push a Matroska A/V stream to voctocore:

.. code-block:: bash

   ffmpeg -i input.mp4 \
     -f matroska -vcodec libx264 -acodec aac \
     tcp://localhost:10000

.. seealso::
   :ref:`common-source-attributes` for the ``scan`` and ``volume`` attributes that apply to all source kinds.
