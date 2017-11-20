# Voctomidi - Control Voctocore from a MIDI controller

## Configuration
Set the `device` option in the `midi` section to the device
you want to connect to. This can be either a device name, or port.
If this is unset or the device can't be found a list of connected devices will
be provided for you to choose from.

In the `eventmap` section MIDI NOTE ON events are mapped to Voctocore layouts.
The syntax is `<note>=<srcA> <srcB> <mode>`.

## AKAI Professional – LPD-8
An example-config is given for an [http://www.akaipro.com/products/pad-controllers/lpd-8|AKAI Professional – LPD-8]
device which is in productive use by the subteam maintaining the voctomidi-bindings.
