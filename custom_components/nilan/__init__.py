"""The Nilan integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import Entity

from .const import (
    BOARD_TYPE_CTS700,
    BOARD_TYPE_CTS700_LEGACY,
    BOARD_TYPE_CTS700_NORDIC,
    DOMAIN,
)
from .device import Device
from .device_cts700 import DeviceCTS700
from .device_cts700_legacy import DeviceCTS700Legacy
from .device_cts700_nordic import DeviceCTS700Nordic
from .modbus_hub_util import build_modbus_hub_name

PLATFORMS = [
    "binary_sensor",
    "button",
    "climate",
    "number",
    "select",
    "sensor",
    "switch",
    "water_heater",
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nilan Modbus from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    name = entry.data["name"]
    host_port = entry.data["host_port"]
    unit_id = entry.data["unit_id"]
    com_type = entry.data["com_type"]
    host_ip = entry.data["host_ip"]
    board_type = entry.data.get("board_type", "CTS602")
    hub_name = build_modbus_hub_name(
        name,
        entry_id=entry.entry_id,
        board_type=board_type,
        unit_id=unit_id,
    )

    if board_type == BOARD_TYPE_CTS700:
        device = DeviceCTS700(
            hass, name, com_type, host_ip, host_port, unit_id, hub_name=hub_name
        )
    elif board_type == BOARD_TYPE_CTS700_LEGACY:
        device = DeviceCTS700Legacy(
            hass, name, com_type, host_ip, host_port, unit_id, hub_name=hub_name
        )
    elif board_type == BOARD_TYPE_CTS700_NORDIC:
        device = DeviceCTS700Nordic(
            hass, name, com_type, host_ip, host_port, unit_id, hub_name=hub_name
        )
    else:
        device = Device(
            hass, name, com_type, host_ip, host_port, unit_id, hub_name=hub_name
        )
    try:
        await device.setup()
    except ValueError as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting {host_ip}") from ex
    hass.data[DOMAIN][entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        new.update({"com_type": "tcp"})
        new.update({"board_type": "CTS602"})
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    elif config_entry.version == 2:
        new = {**config_entry.data}
        new.update({"board_type": "CTS602"})
        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.data[DOMAIN][entry.entry_id].async_close()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class NilanEntity(Entity):
    """Nilan Entity."""

    def __init__(self, device) -> None:
        """Initialize the instance."""
        self._device = device

    def make_unique_id(self, name: str) -> str:
        """Build a unique id scoped to the device, so multiple units do not collide.

        Uses the entry-derived hub name (sanitized entry_id), which is stable
        across reloads and unique even for two identical units set up with the
        same user-facing name/type.
        """
        return f"{self._device.get_hub_name}_{name}"

    @property
    def device_info(self):
        """Device Info."""
        unique_id = self._device.get_device_name + self._device.get_device_type

        return {
            "identifiers": {
                (DOMAIN, unique_id),
            },
            "name": self._device.get_device_name,
            "manufacturer": "Nilan",
            "model": self._device.get_device_type,
            "sw_version": self._device.get_device_sw_version,
            "hw_version": str(self._device.get_device_hw_version),
        }
