# Setup-Time Register Probe + Filter Day Entities

Date: 2026-08-16
Status: Approved design (pending implementation plan)

## Problem

Nilan integration polls registers the connected unit's firmware does not
implement. Every 30 s poll cycle returns Modbus exception code 2 (illegal data
address), logged twice per failed read (`homeassistant.components.modbus` hub
"isError True" + `custom_components.nilan.device` "Could not read get_*"). No
capability detection, no fallback, no backoff — errors repeat every poll
indefinitely, burying real errors.

Confirmed on two units:

- **Compact P RFB XL GEO9** (CTS700 Nordic map, sw 2.03.01.14 / 2018-01-29):
  entire 20xxx holding space rejected (20103, 20164, 20288–20298, 20460,
  21771). 1xxx–5xxx space works, incl. filter counters 1326–1329.
- **Comfort CT200** (CTS602 map, Comfort light, sw 1.1.34.0): input 215
  (T15), holding 123/124 (user functions) rejected.

Manual entity-level disabling of unknown sensors does NOT fix the spam:
enabled entities whose getter still reads a dead register keep logging at the
hub level (e.g. DHW setpoint 20460 read by water_heater; T8 getter reads dead
20296 in addition to live 5159 fallback).

Variants of the same board family support different register subsets. Register
definitions must NOT be deleted — a register dead on one unit may be live on
another. Fix at the poll/gate level, not the definition level.

## Goal

1. Probe uncertain registers once at setup time.
2. Disable (default-off) entities whose registers do not respond.
3. Stop all per-poll ERROR spam for dead registers.
4. Add 1326–1329 filter-day entities (days_to, days_since).
5. Keep every existing register definition — variant-safe.

Scope confirmation (2026-08-16):

- 1326/1327 interval registers ARE included as diagnostic sensors.
- 1326/1327/1328/1329 filter entities added to the **CTS700
  Nordic/Polar/Arctic hybrid map only**.
- Other boards (CTS602, CTS700 2018+, CTS700 2015 legacy): no new entities,
  no register-map changes. Their probe tables gate existing getters so
  nonexistent registers auto-disable.

## Approach

Selected: **Per-board register declarations + central probe helper (A)**.

- Each device class declares which of its getters read *uncertain* registers.
- Shared probe helper runs once in `setup()` after core connection probes.
- Dead registers recorded per device; getters short-circuit on them.
- Entities for fully-unsupported attributes created but disabled by default
  (user can re-enable — option B).

Rejected:
- **B** — central register→supported map + read wrapper. Larger refactor,
  touches every `async_pb_call` site, address collision risk.
- **C** — lazy-only failure backoff. Still emits N errors after each restart;
  does not satisfy setup-time probe requirement.

## Section 1 — Probe core

New file `register_probe.py`.

```python
# Semantics: attribute unsupported iff ALL its candidate registers dead.
# Dead = read raised Modbus exception (exc 2) once during setup probe.
```

Per-device state:

- `self._dead_registers: set[(kind, address)]` — filled by probe, consulted by
  getters.
- `self._unsupported_attributes: set[str]` — derived: all candidate registers
  dead.
- `self.supports_attribute(name) -> bool` — `name not in _unsupported_attributes`.

Probe flow in `setup()` after core probes:

1. For each attribute spec, read each register once.
2. Fail → add `(kind, addr)` to dead set; log once `WARNING` ("register X
   unsupported on this unit — entity may be disabled").
3. After pass, derive `_unsupported_attributes`.
4. Success → silent.

Getter guards — every `_read_holding` / `_read_input` helper checks dead set
first:

```python
async def _read_holding(self, address):
    if ("holding", address) in self._dead_registers:
        return None  # no Modbus call, no hub ERROR log
    ...existing read...
```

Multi-register getters (e.g. T8: input 5159 + holding 20296) keep working:
dead 20296 skipped, live 5159 used.

Kills both spam sources: no call made (hub silent) + getter returns None
without logging (device silent).

## Section 2 — Per-board probe specs

Only *uncertain* registers probed; core/verified registers excluded.

```python
# CTS700 Nordic — user's unit: entire 20xxx space dead; 1xxx-5xxx live.
CTS700_NORDIC_PROBE = {
    "get_average_humidity":                 [("holding", 20164)],
    "get_t4_outlet":                        [("holding", 20288)],
    "get_t5_condenser_temperature":         [("holding", 20290)],
    "get_t6_evaporator_temperature":        [("holding", 20292)],
    "get_t7_inlet_temperature_after_heater":[("holding", 20294)],
    "get_t8_outdoor_temperature":           [("input", 5159), ("holding", 20296)],
    "get_t9_heater_temperature":            [("holding", 20298)],
    "get_fan_speed_percent":                [("holding", 21771)],
    "get_electric_water_heater_setpoint":   [("holding", 20460)],
    "get_days_to_air_filter_change":        [("holding", 1328), ("holding", 20103)],
    "get_days_since_air_filter_change":     [("holding", 1326), ("holding", 1328)],
    "get_filter_interval_inlet":            [("holding", 1326)],    # NEW diagnostic
    "get_filter_interval_exhaust":          [("holding", 1327)],    # NEW diagnostic
}
```

Decisions:

- T8 spec = input 5159 + holding 20296. 20296 probed so dead 20296 is
  dead-guarded; 5159 live keeps entity enabled. If both dead → entity disabled.
- Filter days: 1328 (remaining) primary for Nordic, 20103 probed as fallback.
  1328 live → enabled, 20103 dead-guarded. Both dead → entity disabled.
  Variants with only 20103: probe marks getter unsupported (1328 dead), user
  re-enables, getter fallback serves 20103.
- Other boards get their own probe tables for their own uncertain registers:
  - CTS602: input 215, holding 123, holding 124.
  - 2018+ CTS700: 21771, 20296, 20103 set.
  - Legacy: 1326/1328 pair.
- No register definition is deleted. Dead ones stop being polled only on units
  that lack them; units that have them probe alive and poll normally.

## Section 3 — Filter entities (1326-1329)

New getters on Nordic class:

```python
# 1326 = inlet interval (90), 1328 = inlet remaining (17)
# days_since = 1326 - 1328 = 73 (matches HMI)
# days_to = 1328 = 17

async def get_days_to_air_filter_change(self):
    remaining = await self._read_holding_unsigned(1328)
    if remaining is not None:
        return remaining
    return await self._read_holding_unsigned(20103)  # dead-guarded fallback

async def get_days_since_air_filter_change(self):
    interval = await self._read_holding_unsigned(1326)
    remaining = await self._read_holding_unsigned(1328)
    if interval is None or remaining is None:
        return None
    return max(0, interval - remaining)

async def get_filter_interval_inlet(self):
    return await self._read_holding_unsigned(1326)

async def get_filter_interval_exhaust(self):
    return await self._read_holding_unsigned(1327)
```

Precedence decision: gate `get_days_to_air_filter_change` on 1328 only. 1328 is
verified-live on the reference unit; 20103 never responds there. Hypothetical
20103-only variant: probe disables getter (1328 dead), user re-enables, fallback
serves 20103.

Entity map additions (`device_map_cts700_nordic.py`):

- `get_days_to_air_filter_change`: already present → add 1328 probe entry; keep
  20103 in `registers.py` as dead-guarded fallback.
- `get_days_since_air_filter_change`: NEW sensor → add to `sensor.py`
  `ATTRIBUTE_TO_SENSORS` (days unit, measurement, diagnostic category).
- `get_filter_interval_inlet` (1326) / `get_filter_interval_exhaust` (1327):
  NEW diagnostic sensors, days unit, diagnostic category.

Other boards — **no new entities, no register-map changes**:

- CTS602, CTS700 2018+, CTS700 2015 legacy: probe tables gate existing getters
  only. Nonexistent registers auto-disable. Existing filter behavior untouched
  (legacy 1326/1328 threshold-minus-passed; CTS602 1103/1104; 2018+ 20103).

## Section 4 — Platform integration + error handling

Probe runs in each device class `setup()`, after existing core probes (machine
type, T1/T3), before entity maps finalized. Reuses open Modbus connection,
sequential single-register reads.

`supports_attribute` wiring — each platform's `async_setup_entry`:

```python
enabled = m.enabled and device.supports_attribute(attribute)
```

One-line change per platform: `sensor.py`, `binary_sensor.py`, `number.py`,
`select.py`, `climate.py`, `switch.py`, `water_heater.py`, `button.py`.

Error handling:

- Probe failures: `WARNING` once per dead register at setup.
- `_dead_registers` guard: returns `None` silently — no per-poll ERROR.
- `_unsupported_attributes`: entity `enabled=False` → no polling, no logs.
- Required/core probe failures (machine type, T1): unchanged —
  `ValueError` → `ConfigEntryNotReady`.

Edge cases:

- Unit offline during probe → reads fail (timeout, not exc 2) → same treatment
  (dead/disabled). Probe re-runs on restart/reload → recovers.
- Register partially dead (writes OK, reads fail): probe tests reads only.
  Setters still write; failure logged per call — acceptable, rare.
- `update_before_add=True` in sensor platform polls once at add →
  dead-guarded getter returns None → state unknown, no log spam.

## Section 5 — Testing

Unit tests (pytest + pytest-asyncio, mocked modbus hub):

1. Probe marks dead register — mock `async_pb_call` error for `(holding, 20103)`;
   assert in `_dead_registers`.
2. Attribute unsupported iff all regs dead — 1328 dead → filter getter
   unsupported; T8 with 5159 live → supported despite 20296 dead.
3. Getter guard skips dead register — `_read_holding(20296)` with dead set →
   `None`, `async_pb_call` never awaited (mock assert_not_awaited).
4. Filter math — 1326=90, 1328=17 → `days_since`=73, `days_to`=17.
5. Fallback — 1328 dead, 20103 live → `days_to` = 20103 value.
6. Platform enabled flag — `supports_attribute` False → entity
   `_attr_entity_registry_enabled_default = False`.

Manual smoke test (user's unit):

- Setup probe on live CTS700 Nordic → expect 10 dead 20xxx registers logged
  WARNING once, entities disabled, zero recurring errors.
- T8 sensor still shows value via 5159.
- Filter sensors: `days_to` = 17, `days_since` = 73.
- Interval diagnostics: inlet = 90, exhaust = 90.

## Files touched

- NEW `custom_components/nilan/register_probe.py`
- `custom_components/nilan/device.py` (CTS602 probe + guards)
- `custom_components/nilan/device_cts700.py`
- `custom_components/nilan/device_cts700_legacy.py`
- `custom_components/nilan/device_cts700_nordic.py`
- `custom_components/nilan/device_map_cts700_nordic.py`
- `custom_components/nilan/registers.py` (no deletions; comments only)
- `custom_components/nilan/sensor.py` (days_since map + enabled wiring)
- `custom_components/nilan/binary_sensor.py`
- `custom_components/nilan/number.py`
- `custom_components/nilan/select.py`
- `custom_components/nilan/climate.py`
- `custom_components/nilan/switch.py`
- `custom_components/nilan/water_heater.py`
- `custom_components/nilan/button.py`
- Tests: `tests/test_register_probe.py`
