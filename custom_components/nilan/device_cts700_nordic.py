"""Nilan CTS700 Compact P Køl Polar/Nordic/Arctic (XL) hybrid device.

Hardware: CTS700 LC Board (e.g. v4.0 / NCS-700), product family
Compact P Køl Polar/Nordic/Arctic (XL), varenr 75124xx.

Fan writes use holding 4747 with values 101-104. Do not mix with CTS700 2018+
(21771 percent) or CTS700 2015 legacy (4747 percent).
"""

from __future__ import annotations

import logging

from homeassistant.components.modbus import modbus
from homeassistant.core import HomeAssistant

from .capabilities import (
    capabilities_for_cts700_nordic,
    filter_attributes_by_capabilities,
)
from .device_map_cts700_nordic import CTS700_NORDIC_ENTITY_MAP
from .registers import CTS700NordicRegisters as Reg

_LOGGER = logging.getLogger(__name__)

_TEMP_SCALE = 10

# Nordic holding 5432: 0 off, 1 cool, 2 heat, 3 dehum, 4 DHW
# Climate layer: 1 heat, 2 cool, 3 auto
_NORDIC_TO_CLIMATE = {1: 2, 2: 1, 3: 3, 4: 3}
_CLIMATE_TO_NORDIC = {1: 2, 2: 1, 3: 3}


class DeviceCTS700Nordic:
    """CTS700 Nordic XL hybrid map device."""

    def __init__(
        self,
        hass: HomeAssistant,
        name,
        com_type,
        host_ip: str | None,
        host_port,
        unit_id,
    ) -> None:
        """Create Nordic hybrid device."""
        self.hass = hass
        self._device_name = name
        self._device_type = "Compact P Køl Polar/Nordic/Arctic XL CTS700"
        self._device_sw_ver = ""
        self._device_hw_ver = "CTS700"
        self._host_ip = host_ip
        self._host_port = host_port
        self._unit_id = int(unit_id)
        self._com_type = com_type
        self._client_config = {
            "name": self._device_name,
            "type": self._com_type,
            "method": "rtu",
            "delay": 0,
            "port": self._host_port,
            "timeout": 1,
            "host": self._host_ip,
            "parity": "E",
            "baudrate": 19200,
            "bytesize": 8,
            "stopbits": 1,
        }
        self._modbus = modbus.ModbusHub(self.hass, self._client_config)
        self._attributes = {}
        self._board_type = "CTS700_NORDIC"
        self._capabilities: frozenset[str] = frozenset()

    async def async_close(self):
        """Close modbus connection."""
        await self._modbus.async_close()

    async def setup(self):
        """Modbus and attribute map setup."""
        _LOGGER.debug("CTS700 Nordic setup started")
        success = await self._modbus.async_setup()
        if success:
            await self._modbus.event_connected.wait()
        else:
            await self._modbus.async_close()
            raise ValueError("Modbus setup was unsuccessful")

        probe = await self._read_input(Reg.t3_extract)
        if probe is None:
            await self._modbus.async_close()
            raise ValueError("CTS700 Nordic probe read failed")

        for entity, value in CTS700_NORDIC_ENTITY_MAP.items():
            self._attributes[entity] = value["entity_type"]

        caps = capabilities_for_cts700_nordic()
        self._capabilities = caps
        self._attributes = filter_attributes_by_capabilities(
            self._attributes, CTS700_NORDIC_ENTITY_MAP, caps
        )

        outdoor = await self.get_t1_intake_temperature()
        if outdoor is not None:
            self._device_sw_ver = f"Nordic hybrid; outdoor {outdoor:.1f} C"
        _LOGGER.debug(
            "CTS700 Nordic attributes=%s capabilities=%s",
            list(self._attributes.keys()),
            sorted(caps),
        )

    def get_assigned(self, platform: str):
        """Get platform assignment."""
        return [key for key, value in self._attributes.items() if value == platform]

    @property
    def get_device_name(self):
        """Device name."""
        return self._device_name

    @property
    def get_device_type(self):
        """Device type."""
        return self._device_type

    @property
    def get_device_hw_version(self):
        """Hardware version."""
        return self._device_hw_ver

    @property
    def get_device_sw_version(self):
        """Software version string."""
        return self._device_sw_ver

    @property
    def get_attributes(self):
        """Return device attributes."""
        return self._attributes

    async def _read_holding(self, address: int) -> int | None:
        """Read one holding register as signed int."""
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "holding"
        )
        if result is not None:
            return int.from_bytes(
                result.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=True,
            )
        return None

    async def _read_holding_unsigned(self, address: int) -> int | None:
        """Read one holding register as unsigned int."""
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "holding"
        )
        if result is not None:
            return int.from_bytes(
                result.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=False,
            )
        return None

    async def _read_input(self, address: int) -> int | None:
        """Read one input register as signed int."""
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "input"
        )
        if result is not None:
            return int.from_bytes(
                result.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=True,
            )
        return None

    async def _read_input_unsigned(self, address: int) -> int | None:
        """Read one input register as unsigned int."""
        result = await self._modbus.async_pb_call(
            self._unit_id, address, 1, "input"
        )
        if result is not None:
            return int.from_bytes(
                result.registers[0].to_bytes(2, "little", signed=False),
                "little",
                signed=False,
            )
        return None

    async def _write_holding(self, address: int, value: int) -> None:
        """Write one holding register."""
        await self._modbus.async_pb_call(
            self._unit_id, address, [value], "write_registers"
        )

    async def _read_temp_input(self, address: int) -> float | None:
        """Read input temperature with 0.1 scale."""
        value = await self._read_input(address)
        if value is None:
            return None
        return float(value) / _TEMP_SCALE

    async def _read_temp_holding(self, address: int) -> float | None:
        """Read holding temperature with 0.1 scale."""
        value = await self._read_holding(address)
        if value is None:
            return None
        return float(value) / _TEMP_SCALE

    async def _write_temp(
        self, address: int, celsius: float, min_v: float, max_v: float
    ) -> bool:
        """Write temperature with 0.1 scale."""
        if celsius < min_v or celsius > max_v:
            return False
        raw = int(round(celsius * _TEMP_SCALE))
        output = int.from_bytes(
            raw.to_bytes(2, "little", signed=True), "little", signed=False
        )
        await self._write_holding(address, output)
        return True

    async def _raw_operation_mode(self) -> int | None:
        """Raw Nordic operation mode from 5432."""
        return await self._read_holding_unsigned(Reg.operation_mode)

    def get_climate_fan_modes(self) -> list[str]:
        """Nordic fan steps are 1-4 only (4747 = 101-104). No off via fan 0."""
        return ["1", "2", "3", "4"]

    def get_climate_hvac_modes(self) -> list[str]:
        """Selectable climate modes.

        Holding 5432 reports active cool/heat/dehum/DHW as status on Compact P
        Nordic; heat/cool writes do not stick as user setpoints. Keep Auto + Off.
        """
        return ["auto", "off"]

    def supports_water_heater_off(self) -> bool:
        """Compact P Nordic shared DHW setpoint does not reliably accept 0 as Off."""
        return False

    async def get_run_state(self) -> bool | None:
        """True when unit is not in off mode."""
        mode = await self._raw_operation_mode()
        if mode is None:
            _LOGGER.error("Could not read get_run_state")
            return None
        return mode != 0

    async def set_run_state(self, state: bool) -> None:
        """Turn off (mode 0) or restore auto/dehum (3) when starting from off."""
        if not state:
            await self._write_holding(Reg.operation_mode, 0)
            return
        current = await self._raw_operation_mode()
        if current in (None, 0):
            # 3 = dehum/auto path; controller then picks heat/cool itself
            await self._write_holding(Reg.operation_mode, 3)

    async def get_operation_mode(self) -> int | None:
        """Climate mode for HA mode selector (always auto when running).

        Active heat/cool from 5432 is exposed via get_control_state / hvac_action.
        """
        raw = await self._raw_operation_mode()
        if raw is None:
            _LOGGER.error("Could not read get_operation_mode")
            return None
        return 3

    async def set_operation_mode(self, mode: int) -> bool:
        """Accept Auto only; heat/cool are not user-writable setpoints on Nordic."""
        if mode != 3:
            _LOGGER.debug(
                "Ignoring Nordic HVAC mode %s (selectable modes are auto/off only)",
                mode,
            )
            return False
        # Auto means leave controller strategy alone; do not force 5432 writes
        return True

    async def get_ventilation_step(self) -> int | None:
        """Fan step 1-4 from holding 4747 values 101-104."""
        value = await self._read_holding_unsigned(Reg.user_fan_step)
        if value is None:
            _LOGGER.error("Could not read get_ventilation_step")
            return None
        if 101 <= value <= 104:
            return value - 100
        if value in (1, 2, 3, 4):
            return value
        # Step 0 / unknown: Nordic units do not expose fan-off on 4747
        return 1

    async def set_ventilation_step(self, mode: int) -> bool:
        """Write fan step as 101-104 (levels 1-4 only)."""
        if mode not in (1, 2, 3, 4):
            _LOGGER.debug("Ignoring Nordic fan step %s (valid 1-4)", mode)
            return False
        await self._write_holding(Reg.user_fan_step, 100 + mode)
        return True

    async def get_control_state(self) -> int | None:
        """Approximate control state for climate action UI from raw 5432."""
        running = await self.get_run_state()
        if running is None:
            return None
        if not running:
            return 0
        raw = await self._raw_operation_mode()
        if raw is None:
            return None
        # Nordic 5432: 1 cool, 2 heat, 3 dehum, 4 DHW
        if raw == 2:
            return 7
        if raw == 1:
            return 8
        return 6

    async def get_control_temperature(self) -> float | None:
        """Room / extract air temperature (T3 input)."""
        value = await self._read_temp_input(Reg.t3_extract)
        if value is None:
            _LOGGER.error("Could not read get_control_temperature")
        return value

    async def get_user_temperature_setpoint(self) -> float | None:
        """Room temperature setpoint (4746)."""
        value = await self._read_temp_holding(Reg.user_temperature)
        if value is None:
            _LOGGER.error("Could not read get_user_temperature_setpoint")
        return value

    async def set_user_temperature_setpoint(self, value: float) -> None:
        """Set room temperature setpoint."""
        await self._write_temp(Reg.user_temperature, value, 5, 30)

    async def get_t1_intake_temperature(self) -> float | None:
        """Outdoor air temperature."""
        return await self._read_temp_input(Reg.t1_outdoor)

    async def get_t2_inlet_temperature(self) -> float | None:
        """Supply air temperature."""
        return await self._read_temp_input(Reg.t2_supply)

    async def get_t3_exhaust_temperature(self) -> float | None:
        """Extract air temperature."""
        return await self._read_temp_input(Reg.t3_extract)

    async def get_t4_outlet(self) -> float | None:
        """Exhaust / after heat exchanger."""
        return await self._read_temp_holding(Reg.t4_exhaust)

    async def get_t5_condenser_temperature(self) -> float | None:
        """Condenser / after heat pump."""
        return await self._read_temp_holding(Reg.t5_condenser)

    async def get_t6_evaporator_temperature(self) -> float | None:
        """Evaporator temperature (T6)."""
        return await self._read_temp_holding(Reg.t6_evaporator)

    async def get_t7_inlet_temperature_after_heater(self) -> float | None:
        """Supply after after-heater (T7). None when register unused (~0 C)."""
        value = await self._read_temp_holding(Reg.t7_after_heater)
        if value is None:
            return None
        # Many Compact P Nordic/Polar units have no T7 sensor; bus returns 0.0
        if abs(value) < 0.05:
            return None
        return value

    async def get_t8_outdoor_temperature(self) -> float | None:
        """Polar/Nordic preheater path / T8 (input 5159)."""
        return await self._read_temp_input(Reg.t8_preheater)

    async def get_t9_heater_temperature(self) -> float | None:
        """Water surface / after heater (T9, holding 20298)."""
        return await self._read_temp_holding(Reg.t9_water_surface)

    async def get_humidity(self) -> float | None:
        """Live extract humidity (4716)."""
        value = await self._read_input_unsigned(Reg.humidity_live)
        if value is None:
            _LOGGER.error("Could not read get_humidity")
            return None
        return float(value)

    async def get_average_humidity(self) -> float | None:
        """Long-average humidity (20164)."""
        value = await self._read_holding_unsigned(Reg.average_humidity)
        if value is None:
            return None
        return float(value)

    async def get_days_to_air_filter_change(self) -> int | None:
        """Days until filter change."""
        return await self._read_holding_unsigned(Reg.filter_days)

    async def get_filter_alarm_state(self) -> bool | None:
        """Filter alarm active (input 5168)."""
        value = await self._read_input_unsigned(Reg.filter_alarm)
        if value is None:
            return None
        return bool(value)

    async def get_fan_speed_percent(self) -> int | None:
        """Fan power / max percent (21771)."""
        return await self._read_holding_unsigned(Reg.fan_power_percent)

    async def get_supply_fan_speed(self) -> int | None:
        """Supply fan actual percent."""
        return await self._read_holding_unsigned(Reg.supply_fan_speed)

    async def get_return_fan_speed(self) -> int | None:
        """Extract fan actual percent."""
        return await self._read_holding_unsigned(Reg.extract_fan_speed)

    async def get_anode_state(self) -> int | None:
        """Anode status raw (0/1/2)."""
        return await self._read_holding_unsigned(Reg.anode_status)

    async def get_electric_water_heater_setpoint(self) -> float | None:
        """DHW setpoint."""
        return await self._read_temp_holding(Reg.hot_water_set_point)

    async def set_electric_water_heater_setpoint(self, value: float) -> None:
        """Set DHW setpoint."""
        if value == 0:
            await self._write_holding(Reg.hot_water_set_point, 0)
            return
        await self._write_temp(Reg.hot_water_set_point, value, 5, 85)

    async def get_compressor_water_heater_setpoint(self) -> float | None:
        """Shared DHW setpoint."""
        return await self.get_electric_water_heater_setpoint()

    async def set_compressor_water_heater_setpoint(self, value: float) -> None:
        """Set shared DHW setpoint."""
        await self.set_electric_water_heater_setpoint(value)

    async def get_t11_electric_water_heater_temperature(self) -> float | None:
        """DHW top temperature."""
        return await self._read_temp_input(Reg.t11_dhw_top)

    async def get_t12_compressor_water_heater_temperature(self) -> float | None:
        """DHW bottom temperature."""
        return await self._read_temp_input(Reg.t12_dhw_bottom)

    async def get_electric_water_heater_state(self) -> bool | None:
        """No dedicated el-supplement bit in community map; always False."""
        return False
