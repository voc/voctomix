import dataclasses
from typing import Optional, Any
from unittest.mock import MagicMock


@dataclasses.dataclass
class MockGstStructure:
    _data: dict[str, str]

    def get_boolean(self, fieldname: str) -> tuple[bool, bool]:
        value = self.get_value(fieldname)
        if value is None:
            return False, False
        return True, bool(value)

    def get_double(self, fieldname: str) -> tuple[bool, float]:
        value = self.get_value(fieldname)
        if value is None:
            return False, 0
        try:
            return True, float(value)
        except ValueError:
            return False, 0

    def get_fraction(self, fieldname: str) -> tuple[bool, int, int]:
        value = self.get_string(fieldname)
        if value is None:
            return False, 0, 0
        entries = value.split('/')
        if len(entries) != 2:
            return False, 0, 0
        try:
            numerator, denominator = entries
            return True, int(numerator), int(denominator)
        except ValueError:
            return False, 0, 0

    def get_int(self, fieldname: str) -> tuple[bool, int]:
        value = self.get_value(fieldname)
        if value is None:
            return False, 0
        try:
            return True, int(value)
        except ValueError:
            return False, 0

    def get_int64(self, fieldname: str) -> tuple[bool, int]:
        return self.get_int(fieldname)

    def get_string(self, fieldname: str) -> Optional[str]:
        return self.get_value(fieldname)

    def get_uint(self, fieldname: str) -> tuple[bool, int]:
        ok, value = self.get_int(fieldname)
        if not ok or value < 0:
            return False, 0
        return True, value

    def get_uint64(self, fieldname: str) -> tuple[bool, int]:
        return self.get_uint(fieldname)

    def get_value(self, fieldname: str) -> Optional[Any]:
        if self.has_field(fieldname):
            return self._data[fieldname]
        else:
            return None

    def has_field(self, fieldname: str) -> bool:
        return fieldname in self._data


@dataclasses.dataclass
class MockGstCaps:
    _data: list[MockGstStructure]

    def get_structure(self, index: int):
        return self._data[index]

    @staticmethod
    def from_string(value: str):
        data = {}
        for entry in ("mime=" + value).split(','):
            key, value = entry.split('=', maxsplit=2)
            data[key] = value
        return MockGstCaps([MockGstStructure(data)])


gst_mock = MagicMock()
gst_mock.version.return_value = (1, 24)
gst_mock.Caps = MockGstCaps
gstcontroller_mock = MagicMock()
gstnet_mock = MagicMock()
gobject_mock = MagicMock()
glib_mock = MagicMock()

socket_mock = MagicMock()
args_mock = MagicMock()
