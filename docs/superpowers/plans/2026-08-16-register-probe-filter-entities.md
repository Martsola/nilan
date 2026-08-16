# Register Probe + Filter Entities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Probe uncertain Modbus registers once at setup; auto-disable entities whose registers don't respond; add 1326/1327/1328/1329 filter entities on the CTS700 Nordic map; stop per-poll ERROR spam.

**Architecture:** Shared `register_probe.py` helper runs once per device in `setup()`, recording dead registers + unsupported attributes. Read helpers short-circuit on dead registers (no Modbus call, no log). Platforms AND the static `enabled` flag with `device.supports_attribute(attr)`. Filter getters on Nordic class read 1326/1328 with 20103 fallback.

**Tech Stack:** Home Assistant custom component, pymodbus via HA Modbus hub (`async_pb_call`), pytest + pytest-asyncio for tests.

## Global Constraints

- Register definitions in `registers.py` are NEVER deleted — variants support different subsets.
- Filter entities (1326/1327/1328/1329) added to **CTS700 Nordic/Polar/Arctic hybrid map ONLY**.
- Other boards (CTS602, CTS700 2018+, CTS700 2015 legacy): no new entities, no register-map changes — probe tables gate existing getters only.
- `async_pb_call(unit_id, address, count, kind)` returns `None` on Modbus error (hub already logs it) — never raises.
- Dead register = probe read returned `None`.
- Attribute unsupported = ALL its candidate registers dead.
- No new dependencies beyond pymodbus (runtime) + pytest/pytest-asyncio (dev).
- Probe failure must NOT raise `ConfigEntryNotReady` — only core probes do.

---

### Task 1: register_probe.py — probe helper + probe specs

**Files:**
- Create: `custom_components/nilan/register_probe.py`
- Test: `tests/test_register_probe.py`

**Interfaces:**
- Produces: `PROBE_SPECS: dict[str, dict[str, list[tuple[str, int]]]]` keyed by board type string; `async def run_register_probe(device, spec) -> None`; mutates `device._dead_registers: set[tuple[str,int]]`, `device._unsupported_attributes: set[str]`.

- [ ] **Step 1: Create test scaffolding**

Create `tests/conftest.py`:

```python
"""Shared test fixtures for the Nilan integration."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

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
```

Note: `DeviceCTS700Nordic` exists in current code; fixture replaces its real
modbus hub with a fake after construction (no connection is made).

- [ ] **Step 2: Run tests to verify scaffolding imports**

Run: `python -m pytest tests/ -q`
Expected: no tests collected yet, exit code 5 (no tests run) or 0 with warning. Scaffolding importable.

- [ ] **Step 3: Write failing tests for register_probe**

Create `tests/test_register_probe.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: FAIL — `ModuleNotFoundError: custom_components.nilan.register_probe`

- [ ] **Step 5: Write register_probe.py**

Create `custom_components/nilan/register_probe.py`:

```python
"""Setup-time register probe for the Nilan integration.

Nilan board families (CTS602, CTS700 2018+, CTS700 2015 legacy, CTS700 Nordic
hybrid) share hardware generations but support different register subsets per
firmware variant. Probing every optional register at setup tells the
integration which entities can work on THIS unit. Dead registers are recorded
per device; getters short-circuit on them so no Modbus call (and no error log)
is ever made again. Entity platforms disable-by-default attributes whose
registers did not respond.

Register definitions are never removed here: a register dead on one unit may
be live on another. This file only controls whether it is polled.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Board type key -> {attribute: [(kind, address), ...]}
# kind: "holding" | "input". Only UNCERTAIN registers are listed. Core
# registers (machine type, T1/T3 probes, setpoints) stay out — they are
# required and already fail setup when absent.
PROBE_SPECS: dict[str, dict[str, list[tuple[str, int]]]] = {
    # CTS700 Nordic/Polar/Arctic hybrid (20xxx holding space absent on
    # firmware 2.03.01.14; 1xxx-5xxx space live).
    "CTS700_NORDIC": {
        "get_average_humidity": [("holding", 20164)],
        "get_t4_outlet": [("holding", 20288)],
        "get_t5_condenser_temperature": [("holding", 20290)],
        "get_t6_evaporator_temperature": [("holding", 20292)],
        "get_t7_inlet_temperature_after_heater": [("holding", 20294)],
        "get_t8_outdoor_temperature": [("input", 5159)],  # 20296 optional alt, not gated
        "get_t9_heater_temperature": [("holding", 20298)],
        "get_fan_speed_percent": [("holding", 21771)],
        "get_electric_water_heater_setpoint": [("holding", 20460)],
        "get_days_to_air_filter_change": [("holding", 1328)],
        "get_days_since_air_filter_change": [
            ("holding", 1326),
            ("holding", 1328),
        ],
        "get_filter_interval_inlet": [("holding", 1326)],
        "get_filter_interval_exhaust": [("holding", 1327)],
    },
    # CTS700 2018+ Compact P.
    "CTS700": {
        "get_ventilation_step": [("holding", 21771)],
        "get_t8_outdoor_temperature": [("holding", 20296)],
        "get_days_to_air_filter_change": [("holding", 20103)],
    },
    # CTS700 2015 legacy.
    "CTS700_LEGACY": {
        "get_days_to_air_filter_change": [
            ("holding", 1326),
            ("holding", 1328),
        ],
    },
    # CTS602 (incl. Comfort light).
    "CTS602": {
        "get_t15_user_panel_temperature": [("input", 215)],
        "get_user_function_1_state": [("holding", 123)],
        "get_user_function_2_state": [("holding", 124)],
    },
}


async def run_register_probe(device: Any, spec: dict) -> None:
    """Probe registers once, fill dead/unsupported sets on the device.

    Mutates device._dead_registers (set[(kind, address)]) and
    device._unsupported_attributes (set[str]).
    """
    dead: set[tuple[str, int]] = set()
    for _attr, regs in spec.items():
        for kind, address in regs:
            result = await device._modbus.async_pb_call(
                device._unit_id, address, 1, kind
            )
            if result is None:
                dead.add((kind, address))

    device._dead_registers = dead
    device._unsupported_attributes = {
        attr
        for attr, regs in spec.items()
        if all((kind, address) in dead for kind, address in regs)
    }

    for kind, address in sorted(dead):
        _LOGGER.warning(
            "register %s %s unsupported on this unit — entity may be disabled",
            kind,
            address,
        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: 4 PASS

- [ ] **Step 7: Commit**

```bash
git add tests/conftest.py tests/test_register_probe.py custom_components/nilan/register_probe.py
git commit -m "feat: setup-time register probe with per-board spec tables"
```

---

### Task 2: Nordic device — probe wiring + dead-register guards

**Files:**
- Modify: `custom_components/nilan/device_cts700_nordic.py`

**Interfaces:**
- Consumes: `run_register_probe`, `PROBE_SPECS["CTS700_NORDIC"]` (Task 1)
- Produces: `DeviceCTS700Nordic.supports_attribute(name) -> bool`; `self._dead_registers`, `self._unsupported_attributes` initialized in `__init__`; guarded `_read_holding`, `_read_holding_unsigned`, `_read_input`, `_read_input_unsigned`.

- [ ] **Step 1: Write failing test**

Append to `tests/test_register_probe.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_register_probe.py::test_nordic_guard_skips_dead_register -v`
Expected: FAIL — real Nordic device lacks `_read_holding` dead-register guard (calls fake modbus, records call, assertion `calls == []` fails).

- [ ] **Step 3: Implement guards + probe wiring in device_cts700_nordic.py**

In `__init__` (after `self._capabilities: frozenset[str] = frozenset()` on line 77), add:

```python
        self._dead_registers: set[tuple[str, int]] = set()
        self._unsupported_attributes: set[str] = set()
```

Add `supports_attribute` method after `get_attributes` (line 149):

```python
    def supports_attribute(self, name: str) -> bool:
        """True when the probed registers for this attribute are alive."""
        return name not in self._unsupported_attributes
```

Guard the four read helpers — add at the top of each (lines 151-201):

```python
    async def _read_holding(self, address: int) -> int | None:
        """Read one holding register as signed int."""
        if ("holding", address) in self._dead_registers:
            return None
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "holding"
        )
        ...
```

```python
    async def _read_holding_unsigned(self, address: int) -> int | None:
        """Read one holding register as unsigned int."""
        if ("holding", address) in self._dead_registers:
            return None
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "holding"
        )
        ...
```

```python
    async def _read_input(self, address: int) -> int | None:
        """Read one input register as signed int."""
        if ("input", address) in self._dead_registers:
            return None
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "input"
        )
        ...
```

```python
    async def _read_input_unsigned(self, address: int) -> int | None:
        """Read one input register as unsigned int."""
        if ("input", address) in self._dead_registers:
            return None
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "input"
        )
        ...
```

In `setup()` (after line 115, after capability filtering, before final debug log), add probe:

```python
        from .register_probe import PROBE_SPECS, run_register_probe
        await run_register_probe(self, PROBE_SPECS["CTS700_NORDIC"])
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: all PASS (probe tests + 3 Nordic guard tests)

- [ ] **Step 5: Commit**

```bash
git add custom_components/nilan/device_cts700_nordic.py tests/conftest.py tests/test_register_probe.py
git commit -m "feat(nordic): probe wiring + dead-register guards"
```

---

### Task 3: Nordic filter getters + entity map + sensor maps

**Files:**
- Modify: `custom_components/nilan/device_cts700_nordic.py`, `custom_components/nilan/device_map_cts700_nordic.py`, `custom_components/nilan/sensor.py`

**Interfaces:**
- Produces: `get_days_to_air_filter_change()` (1328 primary, 20103 fallback), `get_days_since_air_filter_change()`, `get_filter_interval_inlet()`, `get_filter_interval_exhaust()`; map entries for `get_days_since_air_filter_change`, `get_filter_interval_inlet`, `get_filter_interval_exhaust`; sensor Maps for interval getters.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_register_probe.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: FAIL — `AttributeError: get_days_since_air_filter_change` (not implemented on Nordic class yet); map assertions fail.

- [ ] **Step 3: Add register constants + implement getters**

In `registers.py`, inside `CTS700NordicRegisters` (after `filter_days = 20103` at line 692), add:

```python
    filter_interval_inlet = 1326
    filter_interval_exhaust = 1327
    filter_remaining_inlet = 1328
    filter_remaining_exhaust = 1329
```

Then in `device_cts700_nordic.py`, replace `get_days_to_air_filter_change` (lines 493-495) with:

```python
    async def get_days_to_air_filter_change(self) -> int | None:
        """Days until filter change (holding 1328 remaining; 20103 fallback)."""
        remaining = await self._read_holding_unsigned(Reg.filter_remaining_inlet)
        if remaining is not None:
            return remaining
        return await self._read_holding_unsigned(Reg.filter_days)

    async def get_days_since_air_filter_change(self) -> int | None:
        """Days since last filter change (interval - remaining)."""
        interval = await self._read_holding_unsigned(Reg.filter_interval_inlet)
        remaining = await self._read_holding_unsigned(Reg.filter_remaining_inlet)
        if interval is None or remaining is None:
            return None
        return max(0, interval - remaining)

    async def get_filter_interval_inlet(self) -> int | None:
        """Inlet filter interval in days (holding 1326)."""
        return await self._read_holding_unsigned(Reg.filter_interval_inlet)

    async def get_filter_interval_exhaust(self) -> int | None:
        """Exhaust filter interval in days (holding 1327)."""
        return await self._read_holding_unsigned(Reg.filter_interval_exhaust)
```

Note: `Reg` = `CTS700NordicRegisters` (already imported as `Reg` at module top).

- [ ] **Step 4: Update entity map**

In `device_map_cts700_nordic.py`, replace `"get_days_to_air_filter_change": {"entity_type": "sensor"},` (line 25) with:

```python
    "get_days_to_air_filter_change": {"entity_type": "sensor"},
    "get_days_since_air_filter_change": {"entity_type": "sensor"},
    "get_filter_interval_inlet": {"entity_type": "sensor"},
    "get_filter_interval_exhaust": {"entity_type": "sensor"},
```

- [ ] **Step 5: Add sensor Maps**

In `sensor.py`, after the existing `get_days_to_air_filter_change` Map block (ends line 313), add:

```python
    "get_filter_interval_inlet": [
        Map(
            "filter_interval_inlet",
            UnitOfTime.DAYS,
            None,
            SensorStateClass.MEASUREMENT,
            EntityCategory.DIAGNOSTIC,
            "mdi:filter-variant",
            True,
        )
    ],
    "get_filter_interval_exhaust": [
        Map(
            "filter_interval_exhaust",
            UnitOfTime.DAYS,
            None,
            SensorStateClass.MEASUREMENT,
            EntityCategory.DIAGNOSTIC,
            "mdi:filter-variant",
            True,
        )
    ],
```

(UnitOfTime imported at line 16 already; EntityCategory at line 18.)

- [ ] **Step 6: Run tests to verify pass**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add custom_components/nilan/device_cts700_nordic.py custom_components/nilan/registers.py custom_components/nilan/device_map_cts700_nordic.py custom_components/nilan/sensor.py tests/test_register_probe.py
git commit -m "feat(nordic): filter interval/remaining/days-since entities"
```

---

### Task 4: Platform gating — disabled-by-default unsupported entities

**Files:**
- Modify: `custom_components/nilan/sensor.py`, `custom_components/nilan/binary_sensor.py`

**Interfaces:**
- Consumes: `device.supports_attribute(attr)` (Tasks 2, and per-board equivalents)
- Produces: entities with `_attr_entity_registry_enabled_default=False` when attribute unsupported.

**Scope note:** number/select/switch/button getters on affected units are all live (no dead-register mappings); climate/water_heater are composite entities and must NOT be gated (Nordic DHW setpoint 20460 dead → water heater would vanish; getter guard alone silences it). Only sensor + binary_sensor get gating.

- [ ] **Step 1: Write failing test**

Append to `tests/test_register_probe.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_register_probe.py::test_sensor_platform_disables_unsupported -v`
Expected: FAIL — enabled defaults True (unchanged).

- [ ] **Step 3: Implement gating**

`sensor.py` — in `async_setup_entry`, change the list comprehension (lines 610-625). Replace:

```python
            sensors.extend(
                [
                    NilanCTS602Sensor(
                        device,
                        attribute,
                        m.name,
                        m.default_unit,
                        m.device_class,
                        m.state_class,
                        m.entity_category,
                        m.icon,
                        m.enabled,
                    )
                    for m in maps
                ]
            )
```

with:

```python
            sensors.extend(
                [
                    NilanCTS602Sensor(
                        device,
                        attribute,
                        m.name,
                        m.default_unit,
                        m.device_class,
                        m.state_class,
                        m.entity_category,
                        m.icon,
                        m.enabled and device.supports_attribute(attribute),
                    )
                    for m in maps
                ]
            )
```

`binary_sensor.py` — same pattern (lines 158-172). Replace `m.enabled,` with `m.enabled and device.supports_attribute(attribute),`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_register_probe.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/nilan/sensor.py custom_components/nilan/binary_sensor.py tests/test_register_probe.py
git commit -m "feat: disable unsupported-register entities by default"
```

---

### Task 5: Other boards — probe wiring + guards (CTS602, 2018+, legacy)

**Files:**
- Modify: `custom_components/nilan/device.py`, `custom_components/nilan/device_cts700.py`, `custom_components/nilan/device_cts700_legacy.py`

**Interfaces:**
- Consumes: `PROBE_SPECS["CTS602"]`, `PROBE_SPECS["CTS700"]`, `PROBE_SPECS["CTS700_LEGACY"]`, `run_register_probe`
- Produces: guarded helpers + `supports_attribute` on each class; probe call in each `setup()`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_register_probe.py`:

```python
from custom_components.nilan.device import Device
from custom_components.nilan.device_cts700 import DeviceCTS700
from custom_components.nilan.device_cts700_legacy import DeviceCTS700Legacy


async def test_cts700_guard_skips_dead(make_fake_device):
    device = make_fake_device({("holding", 20103): None})
    device._dead_registers = {("holding", 20103)}
    assert await device._read_holding_unsigned(20103) is None
    assert device._modbus.calls == []


async def test_legacy_guard_skips_dead(make_fake_device):
    device = make_fake_device({("holding", 1328): None})
    device._dead_registers = {("holding", 1328)}
    assert await device._read_holding_unsigned(1328) is None
    assert device._modbus.calls == []


async def test_all_boards_have_supports_attribute():
    for cls in (Device, DeviceCTS700, DeviceCTS700Legacy, DeviceCTS700Nordic):
        assert hasattr(cls, "supports_attribute")
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_register_probe.py::test_cts700_guard_skips_dead -v`
Expected: FAIL — real DeviceCTS700 built by fixture, no dead-register guard yet (calls modbus, which answers None → returns None but calls recorded). Verify: `device._modbus.calls != []` → assertion fails.

- [ ] **Step 3: Implement guards + probe wiring — device_cts700.py**

In `__init__`, after `self._capabilities` init, add:

```python
        self._dead_registers: set[tuple[str, int]] = set()
        self._unsupported_attributes: set[str] = set()
```

After `get_attributes` property, add `supports_attribute` (same body as Nordic).

Guard `_read_holding` (line 147) and `_read_holding_unsigned` (line 160):

```python
        if ("holding", address) in self._dead_registers:
            return None
```

In `setup()`, after capability filter, add:

```python
        from .register_probe import PROBE_SPECS, run_register_probe
        await run_register_probe(self, PROBE_SPECS["CTS700"])
```

- [ ] **Step 4: Implement guards + probe wiring — device_cts700_legacy.py**

Same three additions: `_dead_registers`/`_unsupported_attributes` in `__init__`, `supports_attribute` method, guard in `_read_holding` (line 151) + `_read_holding_unsigned` (line 164), probe call with `PROBE_SPECS["CTS700_LEGACY"]` at end of `setup()`.

- [ ] **Step 5: Implement guards + probe wiring — device.py (CTS602)**

CTS602 `Device` has no read helper — only the three dead getters are guarded. In `__init__`, add state fields. Add `supports_attribute` after `get_attributes`.

Guard the three getters — each already calls `async_pb_call`; add dead-register check before:

`get_t15_user_panel_temperature` (line 1066): before `result = await self._modbus.async_pb_call(...)` add:

```python
        if ("input", 215) in self._dead_registers:
            return None
```

`get_user_function_1_state` (line 2631): before its `async_pb_call` add:

```python
        if ("holding", 123) in self._dead_registers:
            return None
```

`get_user_function_2_state` (line 2648): before its `async_pb_call` add:

```python
        if ("holding", 124) in self._dead_registers:
            return None
```

In `setup()`, after capability filtering (after line 165), add:

```python
        from .register_probe import PROBE_SPECS, run_register_probe
        await run_register_probe(self, PROBE_SPECS["CTS602"])
```

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add custom_components/nilan/device.py custom_components/nilan/device_cts700.py custom_components/nilan/device_cts700_legacy.py tests/test_register_probe.py
git commit -m "feat: probe wiring + guards on CTS602, CTS700 2018+, legacy"
```

---

### Task 6: Add dev test dependency + docs

**Files:**
- Modify: `requirements.txt`, `changelog/` (new entry per repo convention), `docs/superpowers/specs/2026-08-16-register-probe-filter-entities-design.md` (implementation note)

- [ ] **Step 1: Update requirements.txt**

Append:

```
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 2: Changelog entry**

Follow repo convention — check `changelog/1.3.10.md` for format, add next-version file `changelog/1.3.11.md` describing:

- setup-time register probe, dead registers auto-disable entities (WARNING once at setup, no recurring ERROR spam)
- CTS700 Nordic filter entities: interval (1326/1327), remaining → days-to (1328), days-since (1326−1328)
- no register definitions removed — variant-safe

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add requirements.txt changelog/1.3.11.md
git commit -m "docs: test deps + changelog 1.3.11"
```

---

## Self-Review

**Spec coverage:**
- S1 probe core → Task 1 ✓
- S2 per-board specs → Task 1 (all 4 tables) ✓
- S3 filter getters + maps → Task 3 ✓; Nordic-only ✓ (no other-board filter changes)
- S4 platform gating + error handling → Task 4 (sensor/binary_sensor only — deviation documented: composite water_heater/climate NOT gated, dead-setpoint silenced by guard; number/select/switch/button unaffected) ✓
- S5 tests + smoke → Tasks 1-5 unit tests; smoke test documented as manual step in changelog ✓
- Scope note (interval sensors included, other boards untouched) ✓

**Placeholder scan:** No TBD/TODO; every code step has full content.

**Type consistency:** `run_register_probe(device, spec)`, `supports_attribute(name)`, `_dead_registers: set[tuple[str,int]]`, `_unsupported_attributes: set[str]` used consistently across all tasks. `make_fake_device` fixture (conftest, Task 1) returns a real `DeviceCTS700Nordic` with a fake modbus hub, so probe tests and guard tests exercise real class methods throughout.
