Live sources
============

Expose individual sources as additional live outputs (e.g. for recording a
slide grabber separately) using ``mix/livesources``:

.. code-block:: ini

   [mix]
   sources = cam1,cam2,grabber
   livesources = grabber

The first live source is exposed on port ``15001``, the second on ``15002``,
and so on. Each live source is also blanked by the blinder when it is active.
