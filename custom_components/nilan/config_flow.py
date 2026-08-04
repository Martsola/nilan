"""Config flow for Nilan integration."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
import voluptuous as vol

from homeassistant import config_entries

from .const import BOARD_TYPE_CTS602, BOARD_TYPE_CTS700, DOMAIN
from .device_map import CTS602_DEVICE_TYPES
from .registers import CTS602HoldingRegisters, CTS700NewHoldingRegisters

STEP_TCP_CTS602_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_ip"): str,
        vol.Required("host_port", default="502"): str,
        vol.Required("unit_id", default=30): int,
    }
)

STEP_TCP_CTS700_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_ip"): str,
        vol.Required("host_port", default="502"): str,
        vol.Required("unit_id", default=1): int,
    }
)

STEP_SERIAL_CTS602_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_port"): str,
        vol.Required("unit_id", default=30): int,
    }
)

STEP_SERIAL_CTS700_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_port"): str,
        vol.Required("unit_id", default=1): int,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_validate_cts602(com_type, port, unit_id, address: str | None) -> None:
    """Validate CTS602 device model."""
    if com_type == "tcp":
        client = AsyncModbusTcpClient(
            address,
            port=port,
        )
    else:
        client = AsyncModbusSerialClient(
            port=port,
            stopbits=1,
            bytesize=8,
            parity="E",
            baudrate=19200,
            timeout=1,
        )
    try:
        await client.connect()
        result = await client.read_holding_registers(
            CTS602HoldingRegisters.control_type, count=1, device_id=int(unit_id)
        )
    except ModbusException as value_error:
        client.close()
        raise ValueError("cannot_connect") from value_error
    if hasattr(result, "message"):
        client.close()
        raise ValueError("invalid_response")
    if len(result.registers) == 0:
        client.close()
        raise ValueError("invalid_response")
    value_output = int.from_bytes(
        result.registers[0].to_bytes(2, "little", signed=False),
        "little",
        signed=False,
    )
    if value_output not in CTS602_DEVICE_TYPES:
        _LOGGER.debug(
            "Device Type %s not found in supported devices list",
            str(value_output),
        )
        raise ValueError("unsupported_device")
    client.close()


async def async_validate_cts700(com_type, port, unit_id, address: str | None) -> None:
    """Validate CTS700 by probing outdoor or extract temperature registers."""
    if com_type == "tcp":
        client = AsyncModbusTcpClient(
            address,
            port=port,
        )
    else:
        client = AsyncModbusSerialClient(
            port=port,
            stopbits=1,
            bytesize=8,
            parity="E",
            baudrate=19200,
            timeout=1,
        )
    try:
        await client.connect()
        result = await client.read_holding_registers(
            CTS700NewHoldingRegisters.t1_outdoor_air_temperature,
            count=1,
            device_id=int(unit_id),
        )
    except ModbusException as value_error:
        client.close()
        raise ValueError("cannot_connect") from value_error
    if hasattr(result, "message"):
        client.close()
        raise ValueError("invalid_response")
    if result is None or len(result.registers) == 0:
        client.close()
        raise ValueError("invalid_response")
    client.close()


class NilanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nilan Modbus."""

    VERSION = 3

    data: Optional[dict(str, Any)]

    def __init__(self) -> None:
        """Initialize flow state."""
        self._com_type: str | None = None
        self._board_type: str | None = None

    async def async_step_user(self, user_input: Optional[dict(str, Any)] = None):
        """Invoke when a user initiates a flow via the user interface."""
        return await self.async_step_menu(user_input)

    async def async_step_menu(self, user_input: Optional[dict(str, Any)] = None):
        """Show Communications Selection."""
        return self.async_show_menu(
            step_id="menu",
            menu_options=["tcp", "serial"],
        )

    async def async_step_tcp(self, user_input: Optional[dict(str, Any)] = None):
        """Select board type after choosing TCP."""
        self._com_type = "tcp"
        return await self.async_step_board()

    async def async_step_serial(self, user_input: Optional[dict(str, Any)] = None):
        """Select board type after choosing Serial."""
        self._com_type = "serial"
        return await self.async_step_board()

    async def async_step_board(self, user_input: Optional[dict(str, Any)] = None):
        """Choose CTS602 or CTS700."""
        return self.async_show_menu(
            step_id="board",
            menu_options=["cts602", "cts700"],
        )

    async def async_step_cts602(self, user_input: Optional[dict(str, Any)] = None):
        """CTS602 selected; continue to connection form."""
        self._board_type = BOARD_TYPE_CTS602
        if self._com_type == "serial":
            return await self.async_step_serial_config()
        return await self.async_step_tcp_config()

    async def async_step_cts700(self, user_input: Optional[dict(str, Any)] = None):
        """CTS700 selected; continue to connection form."""
        self._board_type = BOARD_TYPE_CTS700
        if self._com_type == "serial":
            return await self.async_step_serial_config()
        return await self.async_step_tcp_config()

    async def async_step_tcp_config(self, user_input: Optional[dict(str, Any)] = None):
        """Configure ModBus TCP entry."""
        errors: dict(str, str) = {}
        board = self._board_type or BOARD_TYPE_CTS602
        schema = (
            STEP_TCP_CTS700_SCHEMA
            if board == BOARD_TYPE_CTS700
            else STEP_TCP_CTS602_SCHEMA
        )

        if user_input is not None:
            try:
                if board == BOARD_TYPE_CTS700:
                    await async_validate_cts700(
                        "tcp",
                        user_input["host_port"],
                        user_input["unit_id"],
                        user_input["host_ip"],
                    )
                else:
                    await async_validate_cts602(
                        "tcp",
                        user_input["host_port"],
                        user_input["unit_id"],
                        user_input["host_ip"],
                    )
            except ValueError as error:
                errors["base"] = str(error)
            if not errors:
                self.data = user_input
                self.data.update({"com_type": "tcp"})
                self.data.update({"board_type": board})
                return self.async_create_entry(title=user_input["name"], data=self.data)
        return self.async_show_form(
            step_id="tcp_config", data_schema=schema, errors=errors
        )

    async def async_step_serial_config(
        self, user_input: Optional[dict(str, Any)] = None
    ):
        """Configure ModBus Serial RTU entry."""
        errors: dict(str, str) = {}
        board = self._board_type or BOARD_TYPE_CTS602
        schema = (
            STEP_SERIAL_CTS700_SCHEMA
            if board == BOARD_TYPE_CTS700
            else STEP_SERIAL_CTS602_SCHEMA
        )

        if user_input is not None:
            try:
                if board == BOARD_TYPE_CTS700:
                    await async_validate_cts700(
                        "serial", user_input["host_port"], user_input["unit_id"], None
                    )
                else:
                    await async_validate_cts602(
                        "serial", user_input["host_port"], user_input["unit_id"], None
                    )
            except ValueError as error:
                errors["base"] = str(error)
            if not errors:
                self.data = user_input
                self.data.update({"com_type": "serial"})
                self.data.update({"host_ip": None})
                self.data.update({"board_type": board})
                return self.async_create_entry(title=user_input["name"], data=self.data)
        return self.async_show_form(
            step_id="serial_config", data_schema=schema, errors=errors
        )
