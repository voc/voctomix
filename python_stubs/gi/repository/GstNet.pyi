from typing import Any, Optional, Callable

from gi.repository import Gst, GObject, Gio


# https://gstreamer.freedesktop.org/documentation/net/gstnetaddressmeta.html?gi-language=python

class NetAddressMeta(Gst.Meta):
    meta: Gst.Meta
    addr: Gio.SocketAddress

def net_address_meta_get_info() -> Gst.MetaInfo: ...
def buffer_add_net_address_meta(buffer: Gst.Buffer, addr:  Gio.SocketAddress) -> NetAddressMeta: ...
def buffer_get_net_address_meta(buffer: Gst.Buffer) -> NetAddressMeta: ...
def net_address_meta_api_get_type() -> GObject.GType: ...

# https://gstreamer.freedesktop.org/documentation/net/gstnetclientclock.html?gi-language=python

class NetClientClock(Gst.SystemClock):
    class Props(Gst.SystemClock.Props):
        address: str
        base_time: int
        bus: Gst.Bus
        internal_clock: Gst.Clock
        minimum_update_interval: int
        port: int
        qos_dscp: int
        round_trip_limit: int

    props: Props = ...

    clock: Gst.SystemClock = ...

    @staticmethod
    def new(name: str, remote_address: str, remote_port: int, base_time: int) -> 'NetClientClock': ...

# https://gstreamer.freedesktop.org/documentation/net/gstnetcontrolmessagemeta.html?gi-language=python

class NetControlMessageMeta(Gst.Meta):
    meta: Gst.Meta
    message: Gio.SocketControlMessage

def net_control_message_meta_get_info() -> Gst.MetaInfo: ...
def buffer_add_net_control_message_meta(buffer: Gst.Buffer, message: Gio.SocketControlMessage) -> NetControlMessageMeta: ...
def net_control_message_meta_api_get_type() -> GObject.GType: ...

# https://gstreamer.freedesktop.org/documentation/net/gstnettimepacket.html?gi-language=python

NET_TIME_PACKET_SIZE = 16

class NetTimePacket:
    local_time: int = ...
    remote_time: int = ...

    @staticmethod
    def new(buffer: list[int]) -> NetTimePacket: ...

    def copy(self) -> NetTimePacket: ...
    def free(self) -> None: ...
    def send(self, socket: Gio.Socket, dest_address: Gio.SocketAddress) -> bool: ...
    def serialize(self) -> list[int]: ...

def net_time_packet_receive(socket: Gio.Socket) -> tuple[NetTimePacket, Gio.SocketAddress]: ...

# https://gstreamer.freedesktop.org/documentation/net/gstnettimeprovider.html?gi-language=python

class NetTimeProvider(Gst.Object):
    class Props(Gst.Object.Props):
        active: bool
        address: str
        clock: Gst.Clock
        port: int
        qos_dscp: int

    props: Props = ...

    @staticmethod
    def new(clock: Gst.Clock, address: str, port: int) -> 'NetTimeProvider': ...

# https://gstreamer.freedesktop.org/documentation/net/gstnetclientclock.html?gi-language=python#GstNtpClock

class NtpClock(NetClientClock):
    @staticmethod
    def new(name: str, remote_address: str, remote_port: int, base_time: int) -> 'NtpClock': ...

# https://gstreamer.freedesktop.org/documentation/net/gstptpclock.html?gi-language=python

PTP_CLOCK_ID_NONE: int = ...
PTP_STATISTICS_BEST_MASTER_CLOCK_SELECTED: str = "GstPtpStatisticsBestMasterClockSelected"
PTP_STATISTICS_NEW_DOMAIN_FOUND: str = "GstPtpStatisticsNewDomainFound"
PTP_STATISTICS_PATH_DELAY_MEASURED: str = "GstPtpStatisticsPathDelayMeasured"
PTP_STATISTICS_TIME_UPDATED: str = "GstPtpStatisticsTimeUpdated"

class PtpClock(Gst.SystemClock):
    class Props(Gst.SystemClock.Props):
        domain: int
        grandmaster_clock_id: int
        internal_clock: Gst.Clock
        master_clock_id: int

    props: Props = ...

    @staticmethod
    def new(name: str, domain: int) -> 'PtpClock': ...

def ptp_deinit() -> None: ...
def ptp_init(clock_id: int, interfaces: list[str]) -> bool: ...
def ptp_init_full(config: Gst.Structure) -> bool: ...
def ptp_is_initialized() -> bool: ...
def ptp_is_supported() -> bool: ...

PtpStatisticsCallback = Callable[[int, Gst.Structure, Any], bool]
def ptp_statistics_callback_add(callback: Optional[PtpStatisticsCallback] = None, *user_data: Any) -> int: ...
def ptp_statistics_callback_remove(id: int) -> None: ...

# https://gstreamer.freedesktop.org/documentation/net/gstnetutils.html?gi-language=python

def net_utils_set_socket_tos(socket: Gio.Socket, qos_dscp: int) -> bool: ...
