"""Shared test fixtures for the Nilan integration."""
import sys
import types
from pathlib import Path

import pytest
import pytest_socket

# The pytest-homeassistant-custom-component plugin globally disables sockets
# and freezes HA's event-loop policy. On Windows, asyncio event-loop creation
# needs socketpair, so that combination makes every async test error at setup.
# These unit tests don't use HA test helpers, so drop the plugin and restore
# real sockets.
def pytest_configure(config):
    plugin = config.pluginmanager.get_plugin("homeassistant")
    if plugin is not None:
        config.pluginmanager.unregister(plugin)
    pytest_socket.enable_socket()

# A regular `custom_components` package in user site-packages shadows the
# repo's namespace package regardless of sys.path order, so drop any
# conflicting entry before inserting ours.
sys.path = [
    p
    for p in sys.path
    if not Path(p).joinpath("custom_components", "__init__.py").is_file()
]
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))


def _install_modbus_stub():
    """Stub homeassistant.components.modbus before device imports.

    The dev env's pymodbus version mismatches HA's modbus component
    (ModbusResponse import fails), which would break importing the device
    classes. Device classes only need the ModbusHub symbol at import time;
    every test replaces the constructed hub with a fake afterwards.
    """
    modbus_mod = types.ModuleType("homeassistant.components.modbus.modbus")

    class ModbusHub:
        def __init__(self, *args, **kwargs):
            pass

        async def async_setup(self):
            return True

    modbus_mod.ModbusHub = ModbusHub

    pkg = types.ModuleType("homeassistant.components.modbus")
    pkg.modbus = modbus_mod
    sys.modules["homeassistant.components.modbus"] = pkg
    sys.modules["homeassistant.components.modbus.modbus"] = modbus_mod


_install_modbus_stub()

from custom_components.nilan.device_cts700_nordic import DeviceCTS700Nordic


class FakeResult:
    """Minimal pymodbus-style read result."""

    def __init__(self, registers):
        self.registers = registers


@pytest.fixture
def make_fake_device():
    """Real DeviceCTS700Nordic with a fake modbus hub answering from a map."""

    def _make(answers: dict[tuple[str, int], int | None]):
        class FakeModbus:
            def __init__(self):
                self.calls = []

            async def async_pb_call(self, unit_id, address, count, kind):
                self.calls.append((kind, address))
                value = answers.get((kind, address))
                if value is None:
                    return None
                return FakeResult([value])

        device = DeviceCTS700Nordic(
            None,
            "Test",
            "tcp",
            "192.0.2.1",
            "502",
            1,
            hub_name="nilan_hub_test",
        )
        device._modbus = FakeModbus()
        device._dead_registers = set()
        device._unsupported_attributes = set()
        return device

    return _make
