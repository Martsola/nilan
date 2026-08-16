"""Tests for the setup-time register probe."""
import pytest

from custom_components.nilan.register_probe import (
    PROBE_SPECS,
    run_register_probe,
)

SPEC = {
    "get_a": [("holding", 100)],
    "get_b": [("holding", 200), ("holding", 201)],
}


async def test_dead_register_recorded(make_fake_device):
    device = make_fake_device({("holding", 100): None})
    await run_register_probe(device, SPEC)
    assert ("holding", 100) in device._dead_registers
    assert device._unsupported_attributes == {"get_a", "get_b"}


async def test_partial_dead_keeps_attribute_supported(make_fake_device):
    # get_b has two registers; only one dead -> still supported
    device = make_fake_device({("holding", 200): None, ("holding", 201): 5})
    await run_register_probe(device, SPEC)
    assert device._unsupported_attributes == {"get_a"}


async def test_live_register_silent(make_fake_device):
    device = make_fake_device({("holding", 100): 1, ("holding", 200): 2, ("holding", 201): 3})
    await run_register_probe(device, SPEC)
    assert device._dead_registers == set()
    assert device._unsupported_attributes == set()


async def test_probe_specs_cover_all_boards():
    for board, spec in PROBE_SPECS.items():
        assert isinstance(spec, dict)
        for attr, regs in spec.items():
            assert regs, f"{board}:{attr} has empty probe list"
            for kind, addr in regs:
                assert kind in ("holding", "input")
                assert isinstance(addr, int)


from custom_components.nilan.device_cts700_nordic import DeviceCTS700Nordic


async def test_nordic_guard_skips_dead_register(make_fake_device):
    device = make_fake_device({("holding", 20296): None})
    device._dead_registers = {("holding", 20296)}
    value = await device._read_holding(20296)
    assert value is None
    assert device._modbus.calls == []  # no Modbus call made


async def test_nordic_guard_passes_live_register(make_fake_device):
    device = make_fake_device({("holding", 20288): 25})
    value = await device._read_holding(20288)
    assert value == 25
    assert device._modbus.calls == [("holding", 20288)]


async def test_nordic_supports_attribute(make_fake_device):
    device = make_fake_device({})
    device._unsupported_attributes = {"get_average_humidity"}
    assert not device.supports_attribute("get_average_humidity")
    assert device.supports_attribute("get_t1_intake_temperature")


async def test_filter_days_to_remaining(make_fake_device):
    device = make_fake_device({("holding", 1328): 17, ("holding", 1326): 90})
    assert await device.get_days_to_air_filter_change() == 17


async def test_filter_days_to_fallback_20103(make_fake_device):
    # 1328 dead, 20103 live (variant with legacy-style register)
    device = make_fake_device({("holding", 20103): 17})
    device._dead_registers = {("holding", 1328)}
    assert await device.get_days_to_air_filter_change() == 17
    assert ("holding", 20103) in [c for c in device._modbus.calls]


async def test_filter_days_since_math(make_fake_device):
    device = make_fake_device({("holding", 1326): 90, ("holding", 1328): 17})
    assert await device.get_days_since_air_filter_change() == 73


async def test_filter_intervals(make_fake_device):
    device = make_fake_device({("holding", 1326): 90, ("holding", 1327): 90})
    assert await device.get_filter_interval_inlet() == 90
    assert await device.get_filter_interval_exhaust() == 90


async def test_days_since_returns_none_when_interval_missing(make_fake_device):
    device = make_fake_device({("holding", 1328): 17})
    device._dead_registers = {("holding", 1326)}
    assert await device.get_days_since_air_filter_change() is None


async def test_nordic_map_has_filter_entities():
    from custom_components.nilan.device_map_cts700_nordic import (
        CTS700_NORDIC_ENTITY_MAP,
    )
    for name in (
        "get_days_to_air_filter_change",
        "get_days_since_air_filter_change",
        "get_filter_interval_inlet",
        "get_filter_interval_exhaust",
    ):
        assert name in CTS700_NORDIC_ENTITY_MAP


async def test_sensor_maps_have_filter_entities():
    from custom_components.nilan.sensor import ATTRIBUTE_TO_SENSORS
    for name in (
        "get_days_since_air_filter_change",
        "get_filter_interval_inlet",
        "get_filter_interval_exhaust",
    ):
        assert name in ATTRIBUTE_TO_SENSORS


async def test_sensor_platform_disables_unsupported(make_fake_device):
    from custom_components.nilan.sensor import NilanCTS602Sensor

    device = make_fake_device({})
    device._unsupported_attributes = {"get_average_humidity"}
    sensor = NilanCTS602Sensor(
        device,
        "get_average_humidity",
        "average_humidity",
        None,
        None,
        None,
        None,
        None,
        True,
    )
    assert sensor._attr_entity_registry_enabled_default is False


async def test_sensor_platform_keeps_supported(make_fake_device):
    from custom_components.nilan.sensor import NilanCTS602Sensor

    device = make_fake_device({})
    device._unsupported_attributes = set()
    sensor = NilanCTS602Sensor(
        device,
        "get_average_humidity",
        "average_humidity",
        None,
        None,
        None,
        None,
        None,
        True,
    )
    assert sensor._attr_entity_registry_enabled_default is True


from custom_components.nilan.device import Device
from custom_components.nilan.device_cts700 import DeviceCTS700
from custom_components.nilan.device_cts700_legacy import DeviceCTS700Legacy


async def test_cts700_guard_skips_dead(make_fake_device):
    device = make_fake_device({("holding", 20103): None}, cls=DeviceCTS700)
    device._dead_registers = {("holding", 20103)}
    assert await device._read_holding_unsigned(20103) is None
    assert device._modbus.calls == []


async def test_legacy_guard_skips_dead(make_fake_device):
    device = make_fake_device({("holding", 1328): None}, cls=DeviceCTS700Legacy)
    device._dead_registers = {("holding", 1328)}
    assert await device._read_holding_unsigned(1328) is None
    assert device._modbus.calls == []


async def test_all_boards_have_supports_attribute():
    for cls in (Device, DeviceCTS700, DeviceCTS700Legacy, DeviceCTS700Nordic):
        assert hasattr(cls, "supports_attribute")


async def test_nordic_t8_spec_guards_dead_20296(make_fake_device):
    from custom_components.nilan.register_probe import (
        PROBE_SPECS,
        run_register_probe,
    )

    # 20xxx space dead, 5159 live
    answers = {
        ("holding", 20164): None, ("holding", 20288): None,
        ("holding", 20290): None, ("holding", 20292): None,
        ("holding", 20294): None, ("holding", 20296): None,
        ("holding", 20298): None, ("holding", 21771): None,
        ("holding", 20460): None, ("holding", 1328): 17,
        ("holding", 1326): 90, ("holding", 1327): 90,
        ("input", 5159): 196,
    }
    device = make_fake_device(answers)
    await run_register_probe(device, PROBE_SPECS["CTS700_NORDIC"])
    assert ("holding", 20296) in device._dead_registers
    assert device.supports_attribute("get_t8_outdoor_temperature")
    calls_before = len(device._modbus.calls)
    t8 = await device.get_t8_outdoor_temperature()
    assert t8 == 19.6  # 5159 raw 196 / 10 scale
    assert ("holding", 20296) not in [c for c in device._modbus.calls[calls_before:]]


async def test_cts602_t15_guard_skips_dead(make_fake_device):
    from custom_components.nilan.device import Device

    device = make_fake_device({("input", 215): None}, cls=Device)
    device._dead_registers = {("input", 215)}
    assert await device.get_t15_user_panel_temperature() is None
    assert device._modbus.calls == []


async def test_cts602_user_func_1_guard_skips_dead(make_fake_device):
    from custom_components.nilan.device import Device

    device = make_fake_device({("holding", 123): None}, cls=Device)
    device._dead_registers = {("holding", 123)}
    assert await device.get_user_function_1_state() is None
    assert device._modbus.calls == []


async def test_cts602_user_func_2_guard_skips_dead(make_fake_device):
    from custom_components.nilan.device import Device

    device = make_fake_device({("holding", 124): None}, cls=Device)
    device._dead_registers = {("holding", 124)}
    assert await device.get_user_function_2_state() is None
    assert device._modbus.calls == []
