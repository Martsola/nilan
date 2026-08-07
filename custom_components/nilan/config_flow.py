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

STEP_TCP_DETECT_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_ip"): str,
        vol.Required("host_port", default="502"): str,
        vol.Optional("unit_id"): int,
    }
)

STEP_SERIAL_DETECT_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="Nilan"): str,
        vol.Required("host_port"): str,
        vol.Optional("unit_id"): int,
    }
)

# Scaled CTS700 temps (register / 10). Plausible outdoor/extract band.
_CTS700_TEMP_MIN = -40.0
_CTS700_TEMP_MAX = 80.0

_LOGGER = logging.getLogger(__name__)


def _holding_u16(registers: list) -> int | None:
    """Decode first holding register as unsigned little-endian."""
    if not registers:
        return None
    return int.from_bytes(
        registers[0].to_bytes(2, "little", signed=False),
        "little",
        signed=False,
    )


def _holding_s16_temp(registers: list) -> float | None:
    """Decode first holding register as signed temp with 0.1 scale."""
    if not registers:
        return None
    raw = int.from_bytes(
        registers[0].to_bytes(2, "little", signed=False),
        "little",
        signed=True,
    )
    return float(raw) / 10.0


async def _open_client(com_type: str, port, address: str | None):
    """Create and connect a Modbus client."""
    if com_type == "tcp":
        client = AsyncModbusTcpClient(address, port=port)
    else:
        client = AsyncModbusSerialClient(
            port=port,
            stopbits=1,
            bytesize=8,
            parity="E",
            baudrate=19200,
            timeout=1,
        )
    await client.connect()
    return client


async def async_validate_cts602(com_type, port, unit_id, address: str | None) -> int:
    """Validate CTS602 device model. Returns type id."""
    client = await _open_client(com_type, port, address)
    try:
        result = await client.read_holding_registers(
            CTS602HoldingRegisters.control_type, count=1, device_id=int(unit_id)
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
    value_output = _holding_u16(result.registers)
    client.close()
    if value_output is None or value_output not in CTS602_DEVICE_TYPES:
        _LOGGER.debug(
            "Device Type %s not found in supported devices list",
            str(value_output),
        )
        raise ValueError("unsupported_device")
    return value_output


async def async_validate_cts700(com_type, port, unit_id, address: str | None) -> None:
    """Validate CTS700 by probing outdoor temperature register."""
    client = await _open_client(com_type, port, address)
    try:
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
    temp = _holding_s16_temp(result.registers)
    client.close()
    if temp is None or temp < _CTS700_TEMP_MIN or temp > _CTS700_TEMP_MAX:
        raise ValueError("invalid_response")


async def async_detect_board(
    com_type: str, port, address: str | None, unit_id: int | None
) -> dict[str, Any]:
    """Probe CTS602 then CTS700. Returns board_type, unit_id, model."""
    candidates: list[int] = []
    if unit_id is not None:
        candidates.append(int(unit_id))
    for default_id in (1, 30):
        if default_id not in candidates:
            candidates.append(default_id)

    last_error = "cannot_detect"
    for candidate in candidates:
        try:
            type_id = await async_validate_cts602(com_type, port, candidate, address)
            return {
                "board_type": BOARD_TYPE_CTS602,
                "unit_id": candidate,
                "model": CTS602_DEVICE_TYPES[type_id],
                "type_id": type_id,
            }
        except ValueError as err:
            last_error = str(err)
            _LOGGER.debug("CTS602 probe unit_id=%s failed: %s", candidate, err)

        try:
            await async_validate_cts700(com_type, port, candidate, address)
            return {
                "board_type": BOARD_TYPE_CTS700,
                "unit_id": candidate,
                "model": "Compact P CTS700",
                "type_id": None,
            }
        except ValueError as err:
            last_error = str(err)
            _LOGGER.debug("CTS700 probe unit_id=%s failed: %s", candidate, err)

    raise ValueError(last_error if last_error else "cannot_detect")


class NilanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nilan Modbus."""

    VERSION = 3

    data: Optional[dict[str, Any]]

    def __init__(self) -> None:
        """Initialize flow state."""
        self._com_type: str | None = None
        self._board_type: str | None = None
        self._detect_result: dict[str, Any] | None = None
        self._pending_user_input: dict[str, Any] | None = None

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None):
        """Invoke when a user initiates a flow via the user interface."""
        return await self.async_step_menu(user_input)

    async def async_step_menu(self, user_input: Optional[dict[str, Any]] = None):
        """Show Communications Selection."""
        return self.async_show_menu(
            step_id="menu",
            menu_options=["tcp", "serial"],
        )

    async def async_step_tcp(self, user_input: Optional[dict[str, Any]] = None):
        """Select board type after choosing TCP."""
        self._com_type = "tcp"
        return await self.async_step_board()

    async def async_step_serial(self, user_input: Optional[dict[str, Any]] = None):
        """Select board type after choosing Serial."""
        self._com_type = "serial"
        return await self.async_step_board()

    async def async_step_board(self, user_input: Optional[dict[str, Any]] = None):
        """Choose auto-detect, CTS602, or CTS700."""
        return self.async_show_menu(
            step_id="board",
            menu_options=["auto_detect", "cts602", "cts700"],
        )

    async def async_step_auto_detect(self, user_input: Optional[dict[str, Any]] = None):
        """Connection form for auto-detect."""
        if self._com_type == "serial":
            return await self.async_step_serial_detect()
        return await self.async_step_tcp_detect()

    async def async_step_tcp_detect(self, user_input: Optional[dict[str, Any]] = None):
        """TCP connection details then probe board type."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                detected = await async_detect_board(
                    "tcp",
                    user_input["host_port"],
                    user_input["host_ip"],
                    user_input.get("unit_id"),
                )
            except ValueError as error:
                code = str(error)
                if code not in (
                    "cannot_connect",
                    "invalid_response",
                    "unsupported_device",
                    "cannot_detect",
                ):
                    code = "cannot_detect"
                errors["base"] = code
            if not errors:
                self._pending_user_input = {
                    "name": user_input["name"],
                    "host_ip": user_input["host_ip"],
                    "host_port": user_input["host_port"],
                    "com_type": "tcp",
                }
                self._detect_result = detected
                return await self.async_step_confirm()
        return self.async_show_form(
            step_id="tcp_detect",
            data_schema=STEP_TCP_DETECT_SCHEMA,
            errors=errors,
        )

    async def async_step_serial_detect(
        self, user_input: Optional[dict[str, Any]] = None
    ):
        """Serial connection details then probe board type."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                detected = await async_detect_board(
                    "serial",
                    user_input["host_port"],
                    None,
                    user_input.get("unit_id"),
                )
            except ValueError as error:
                code = str(error)
                if code not in (
                    "cannot_connect",
                    "invalid_response",
                    "unsupported_device",
                    "cannot_detect",
                ):
                    code = "cannot_detect"
                errors["base"] = code
            if not errors:
                self._pending_user_input = {
                    "name": user_input["name"],
                    "host_port": user_input["host_port"],
                    "host_ip": None,
                    "com_type": "serial",
                }
                self._detect_result = detected
                return await self.async_step_confirm()
        return self.async_show_form(
            step_id="serial_detect",
            data_schema=STEP_SERIAL_DETECT_SCHEMA,
            errors=errors,
        )

    async def async_step_confirm(self, user_input: Optional[dict[str, Any]] = None):
        """Confirm auto-detect result or fall back to manual board choice."""
        detected = self._detect_result or {}
        pending = self._pending_user_input or {}
        if user_input is not None:
            action = user_input.get("action", "accept")
            if action == "manual":
                self._detect_result = None
                self._pending_user_input = None
                return await self.async_step_board()
            self.data = {
                **pending,
                "unit_id": detected["unit_id"],
                "board_type": detected["board_type"],
            }
            return self.async_create_entry(title=pending["name"], data=self.data)

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("action", default="accept"): vol.In(
                        ["accept", "manual"]
                    ),
                }
            ),
            description_placeholders={
                "board_type": str(detected.get("board_type", "")),
                "model": str(detected.get("model", "")),
                "unit_id": str(detected.get("unit_id", "")),
            },
        )

    async def async_step_cts602(self, user_input: Optional[dict[str, Any]] = None):
        """CTS602 selected; continue to connection form."""
        self._board_type = BOARD_TYPE_CTS602
        if self._com_type == "serial":
            return await self.async_step_serial_config()
        return await self.async_step_tcp_config()

    async def async_step_cts700(self, user_input: Optional[dict[str, Any]] = None):
        """CTS700 selected; continue to connection form."""
        self._board_type = BOARD_TYPE_CTS700
        if self._com_type == "serial":
            return await self.async_step_serial_config()
        return await self.async_step_tcp_config()

    async def async_step_tcp_config(self, user_input: Optional[dict[str, Any]] = None):
        """Configure ModBus TCP entry."""
        errors: dict[str, str] = {}
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
        self, user_input: Optional[dict[str, Any]] = None
    ):
        """Configure ModBus Serial RTU entry."""
        errors: dict[str, str] = {}
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
