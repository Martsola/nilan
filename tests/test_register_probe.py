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
