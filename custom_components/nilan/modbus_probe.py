"""Modbus probe helpers for Nilan config flow."""

from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import BOARD_TYPE_CTS602, BOARD_TYPE_CTS700, BOARD_TYPE_CTS700_LEGACY
from .device_map import CTS602_DEVICE_TYPES
from .registers import (
    CTS602HoldingRegisters,
    CTS700LegacyHoldingRegisters,
    CTS700NewHoldingRegisters,
)

# Scaled CTS700 temps (register / 10). Plausible outdoor/extract band.
_CTS700_TEMP_MIN = -40.0
_CTS700_TEMP_MAX = 80.0

_LOGGER = logging.getLogger(__name__)


def holding_u16(registers: list) -> int | None:
    """Decode first holding register as unsigned little-endian."""
    if not registers:
        return None
    return int.from_bytes(
        registers[0].to_bytes(2, "little", signed=False),
        "little",
        signed=False,
    )


def holding_s16_temp(registers: list) -> float | None:
    """Decode first holding register as signed temp with 0.1 scale."""
    if not registers:
        return None
    raw = int.from_bytes(
        registers[0].to_bytes(2, "little", signed=False),
        "little",
        signed=True,
    )
    return float(raw) / 10.0


async def open_client(com_type: str, port, address: str | None):
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
    client = await open_client(com_type, port, address)
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
    value_output = holding_u16(result.registers)
    client.close()
    if value_output is None or value_output not in CTS602_DEVICE_TYPES:
        _LOGGER.debug(
            "Device Type %s not found in supported devices list",
            str(value_output),
        )
        raise ValueError("unsupported_device")
    return value_output


async def async_validate_cts700(com_type, port, unit_id, address: str | None) -> None:
    """Validate CTS700 (2018+ map) by probing outdoor temperature register."""
    client = await open_client(com_type, port, address)
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
    temp = holding_s16_temp(result.registers)
    client.close()
    if temp is None or temp < _CTS700_TEMP_MIN or temp > _CTS700_TEMP_MAX:
        raise ValueError("invalid_response")


async def async_validate_cts700_legacy(
    com_type, port, unit_id, address: str | None
) -> None:
    """Validate CTS700 2015 map via T1 and user setpoint registers."""
    client = await open_client(com_type, port, address)
    try:
        outdoor = await client.read_holding_registers(
            CTS700LegacyHoldingRegisters.tsens1,
            count=1,
            device_id=int(unit_id),
        )
        setpoint = await client.read_holding_registers(
            CTS700LegacyHoldingRegisters.user_temperature,
            count=1,
            device_id=int(unit_id),
        )
    except ModbusException as value_error:
        client.close()
        raise ValueError("cannot_connect") from value_error
    if hasattr(outdoor, "message") or hasattr(setpoint, "message"):
        client.close()
        raise ValueError("invalid_response")
    if (
        outdoor is None
        or setpoint is None
        or len(outdoor.registers) == 0
        or len(setpoint.registers) == 0
    ):
        client.close()
        raise ValueError("invalid_response")
    outdoor_c = holding_s16_temp(outdoor.registers)
    setpoint_c = holding_s16_temp(setpoint.registers)
    client.close()
    if outdoor_c is None or outdoor_c < _CTS700_TEMP_MIN or outdoor_c > _CTS700_TEMP_MAX:
        raise ValueError("invalid_response")
    if setpoint_c is None or setpoint_c < 5.0 or setpoint_c > 50.0:
        raise ValueError("invalid_response")


def is_cts700_schema_board(board: str) -> bool:
    """True when board uses CTS700 TCP/Serial defaults (unit id 1)."""
    return board in (BOARD_TYPE_CTS700, BOARD_TYPE_CTS700_LEGACY)


async def async_detect_board(
    com_type: str, port, address: str | None, unit_id: int | None
) -> dict[str, Any]:
    """Probe CTS602, CTS700 2018+, then CTS700 2015. Returns board info."""
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
                "model": "Compact P CTS700 (2018+ map)",
                "type_id": None,
            }
        except ValueError as err:
            last_error = str(err)
            _LOGGER.debug("CTS700 probe unit_id=%s failed: %s", candidate, err)

        try:
            await async_validate_cts700_legacy(com_type, port, candidate, address)
            return {
                "board_type": BOARD_TYPE_CTS700_LEGACY,
                "unit_id": candidate,
                "model": "CTS700 (2015 map)",
                "type_id": None,
            }
        except ValueError as err:
            last_error = str(err)
            _LOGGER.debug("CTS700 legacy probe unit_id=%s failed: %s", candidate, err)

    raise ValueError(last_error if last_error else "cannot_detect")
