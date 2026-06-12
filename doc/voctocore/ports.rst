Network Ports
=============

All ports are plain TCP unless noted otherwise.

Control and clock ports
-----------------------

``9998`` (IN, UDP)
   GStreamer NetTimeProvider — clients use this to synchronise their
   pipeline clock with voctocore. Required for any client that sends or
   receives A/V streams (TCP sources, ffmpeg sinks, voctogui previews).

``9999`` (IN)
   Control interface. voctogui and other clients (e.g. voctoremote, voctomidi)
   connect here to send commands and receive state updates.

Source input ports
------------------

``10000+`` (IN)
   TCP A/V sources (``kind = tcp``). Assigned sequentially in the order
   sources appear in ``mix/sources``. First TCP source → ``10000``,
   second → ``10001``, and so on.

``14000`` (IN)
   Overlay source port.

``16000+`` (IN)
   Background source input ports. Assigned sequentially per background source.

``17000+`` (IN)
   Blinder video source ports. Assigned sequentially per blinder video source.

``18000`` (IN)
   Audio blinder source port.

Mix output ports
----------------

``11000`` (OUT)
   Mix recording output (raw Matroska A/V). Full-quality mix used for
   recording.

``11100`` (OUT)
   Mix preview output (encoded, lower resolution). Used by voctogui to display
   the mix preview.

Source output ports
-------------------

``13000+`` (OUT)
   Raw source output mirrors. Assigned sequentially per source. Used by
   voctogui when previews are disabled and the GUI runs on the same machine.

``13100+`` (OUT)
   Encoded source previews (when ``previews/enabled = true``). Assigned
   sequentially per source.

Live output ports
-----------------

``15000`` (OUT)
   Mix live output (blinder-controlled). The stream sent to live audiences;
   blanked when the blinder is active.

``15100`` (OUT)
   Mix live preview output.

``15001+`` (OUT)
   Extra live source outputs (``mix/livesources``). Assigned sequentially.

Other ports
-----------

``19000`` (OUT)
   Local playout output.

``20000`` (OUT)
   Metrics served in prometheus format.

Viewing port assignments
------------------------

voctogui can show the current port assignment table. Enable the ports panel
via ``toolbar/ports = true`` in the configuration or use the toolbar button
if it is visible.

You can also query port state from the control interface (port ``9999``) by
sending the command ``report_ports``.
