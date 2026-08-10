"""Modbus hub naming helpers for the Nilan integration.

YAML Modbus hubs named bare ``nilan`` collide with this integration's domain
and can blank config-flow translation menus in Home Assistant. Always use a
prefixed hub name for the private ModbusHub created by Nilan devices.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_RESERVED_HUB_NAMES = frozenset({"nilan", "modbus", DOMAIN})


def sanitize_hub_token(value: str | None, fallback: str = "device") -> str:
    """Return a lowercase alnum/underscore token for hub names."""
    raw = "".join(c if c.isalnum() else "_" for c in (value or "").lower())
    token = "_".join(part for part in raw.split("_") if part) or fallback
    if token in _RESERVED_HUB_NAMES:
        return f"{fallback}_{token}"
    return token


def build_modbus_hub_name(
    device_name: str | None = None,
    *,
    entry_id: str | None = None,
    board_type: str | None = None,
    unit_id: int | None = None,
) -> str:
    """Build a unique Modbus hub name that never equals bare ``nilan``.

    Prefer ``entry_id`` when available so reloads stay stable and never clash
    with a YAML hub named ``nilan``.
    """
    if entry_id:
        safe_id = sanitize_hub_token(entry_id, fallback="entry")
        return f"nilan_hub_{safe_id}"

    parts = ["nilan_hub", sanitize_hub_token(device_name, fallback="device")]
    if board_type:
        parts.append(sanitize_hub_token(board_type, fallback="board"))
    if unit_id is not None:
        parts.append(str(int(unit_id)))
    return "_".join(parts)


def list_modbus_hub_names(hass: HomeAssistant) -> list[str]:
    """Return configured Modbus hub names (YAML / Modbus integration)."""
    hubs = hass.data.get("modbus")
    if isinstance(hubs, dict):
        return [str(name) for name in hubs]
    return []


def find_conflicting_modbus_hub(hass: HomeAssistant) -> str | None:
    """Return a YAML/core Modbus hub name that can break Nilan UI, if any."""
    for name in list_modbus_hub_names(hass):
        if name.lower() == "nilan":
            return name
    return None


def coexistence_warning(hass: HomeAssistant) -> str:
    """Short operator warning for config-flow descriptions."""
    conflict = find_conflicting_modbus_hub(hass)
    parts: list[str] = []
    if conflict:
        parts.append(
            f"A Modbus hub is named '{conflict}'. Rename it (for example "
            "nilan_compactpc) so Nilan setup menus show labels correctly."
        )
    parts.append(
        "Do not run YAML Modbus and this Nilan integration against the same "
        "unit at the same time (overlapping sessions cause flaky reads)."
    )
    return " ".join(parts)
