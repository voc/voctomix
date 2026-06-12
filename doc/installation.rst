Installation
============

voctomix runs on Linux. It is tested on Debian stable and Ubuntu LTS.
GStreamer 1.14 or later is required.

Clone the repository
--------------------

.. code-block:: bash

   git clone https://github.com/voc/voctomix.git
   cd voctomix

Dependencies
------------

Debian / Ubuntu
```````````````

.. code-block:: bash

   sudo apt install \
     gir1.2-gst-plugins-base-1.0 \
     gir1.2-gstreamer-1.0 \
     gstreamer1.0-libav \
     gstreamer1.0-plugins-bad \
     gstreamer1.0-plugins-base \
     gstreamer1.0-plugins-good \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-tools \
     gstreamer1.0-vaapi \
     gstreamer1.0-x \
     libgstreamer1.0-0 \
     python3-gi \
     python3-pyinotify \
     python3-scipy \
     python3-sdnotify \
     python3-prometheus-client \
     rlwrap

For VAAPI hardware en-/decoding
````````````````````````````````

.. code-block:: bash

   sudo apt install gstreamer1.0-vaapi

Optional (for example scripts)
```````````````````````````````

.. code-block:: bash

   sudo apt install fbset ffmpeg netcat

Developer setup
---------------

voctomix uses `uv <https://github.com/astral-sh/uv>`_ for development:

.. code-block:: bash

   uv venv --system-site-packages
   uv pip install pygobject-stubs --config-settings=config=Gtk3,Gdk3
   uv sync --dev

Running tests
-------------

.. code-block:: bash

   uv run pytest
   uv run mypy -p voctocore -p voctogui
