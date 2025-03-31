import enum

from gi.repository import Gst, GLib


# https://gstreamer.freedesktop.org/documentation/controller/gsttimedvaluecontrolsource.html?gi-language=python

class ControlPoint:
    timestamp: int = ...
    value: float = ...

    def copy(self) -> ControlPoint: ...
    def free(self) -> None: ...

class TimedValueControlSource(Gst.ControlSource):
    class Props(Gst.ControlSource.Props): ...

    parent: Gst.ControlSource = ...
    props: Props = ...

    lock: GLib.Mutex = ...
    values: list[Gst.TimedValue] = ...
    nvalues: int = ...
    valid_cache: bool = ...

    def find_control_point_iter(self, timestamp: int) -> GLib.SequenceIter: ...
    def get_all(self) -> list[Gst.TimedValue]: ...
    def get_count(self) -> int: ...
    def set(self, timestamp: int, value: float) -> bool: ...
    def set_from_list(self, timedvalues: list[Gst.TimedValue]) -> bool: ...
    def unset(self, timestamp: int) -> bool: ...
    def unset_all(self) -> bool: ...

def timed_value_control_invalidate_cache(source: TimedValueControlSource) -> None: ...

# https://gstreamer.freedesktop.org/documentation/controller/gstinterpolationcontrolsource.html?gi-language=python

class InterpolationControlSource(TimedValueControlSource):
    class Props(TimedValueControlSource.Props):
        mode: InterpolationMode

    parent: TimedValueControlSource = ...
    props: Props = ...

    @staticmethod
    def new() -> InterpolationControlSource: ...

class InterpolationMode(enum.IntEnum):
    NONE = 0
    LINEAR = 1
    CUBIC = 2
    CUBIC_MONOTONIC = 3

# https://gstreamer.freedesktop.org/documentation/controller/gsttriggercontrolsource.html?gi-language=python

class TriggerControlSource(TimedValueControlSource):
    class Props(TimedValueControlSource.Props):
        tolerance: int

    parent: TimedValueControlSource = ...
    props: Props = ...

    @staticmethod
    def new() -> TriggerControlSource: ...

# https://gstreamer.freedesktop.org/documentation/controller/gstlfocontrolsource.html?gi-language=python

class LFOControlSource(Gst.ControlSource):
    class Props(Gst.ControlSource.Props):
        amplitude: float
        frequency: float
        offset: float
        timeshift: int
        waveform: LFOWaveform

    parent: Gst.ControlSource = ...
    props: Props = ...

    @staticmethod
    def new() -> LFOControlSource: ...

class LFOWaveform(enum.IntEnum):
    SINE = 0
    SQUARE = 1
    SAW = 2
    REVERSE_SAW = 3
    TRIANGLE = 4

# https://gstreamer.freedesktop.org/documentation/controller/gstargbcontrolbinding.html?gi-language=python

class ARGBControlBinding(Gst.ControlBinding):
    class Props(Gst.ControlBinding.Props):
        control_source_a: Gst.ControlSource
        control_source_r: Gst.ControlSource
        control_source_g: Gst.ControlSource
        control_source_b: Gst.ControlSource

    parent: Gst.ControlBinding = ...
    props: Props = ...

    @staticmethod
    def new(object: Gst.Object, property_name: str, cs_a: Gst.ControlSource, cs_r: Gst.ControlSource, cs_g: Gst.ControlSource, cs_b: Gst.ControlSource) -> ARGBControlBinding: ...

# https://gstreamer.freedesktop.org/documentation/controller/gstdirectcontrolbinding.html?gi-language=python

class DirectControlBinding(Gst.ControlBinding):
    class Props(Gst.ControlBinding.Props):
        absolute: bool
        control_source: Gst.ControlSource

    parent: Gst.ControlBinding = ...
    props: Props = ...

    @staticmethod
    def new(object: Gst.Object, property_name: str, cs: Gst.ControlSource) -> DirectControlBinding: ...

    @staticmethod
    def new_absolute(object: Gst.Object, property_name: str, cs: Gst.ControlSource) -> DirectControlBinding: ...

# https://gstreamer.freedesktop.org/documentation/controller/gstproxycontrolbinding.html?gi-language=python

class ProxyControlBinding(Gst.ControlBinding):
    @staticmethod
    def new(object: Gst.Object, property_name: str, ref_object: Gst.Object, ref_property_name: str) -> ProxyControlBinding: ...


