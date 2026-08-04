# Compact P (CTS700)

Community-tested MVP for **Compact P** with a **CTS700** controller over Ethernet Modbus TCP.

## Hardware

- Cable: Cat5e or better from CTS700 **LAN** port to your router
- Protocol: Modbus TCP
- Port: **502**
- Unit id: **1** (indoor; confirm on your unit)
- Example host in public docs only: `192.168.1.50`

No RS485 bridge is required for native Ethernet CTS700.

## Home Assistant setup

1. Install from HACS or copy `custom_components/nilan` from this fork (`master`).
2. Add **Nilan** integration.
3. Choose **TCP**.
4. Choose **CTS700 (Compact P MVP)**.
5. Enter IP, port `502`, unit id `1`.

## Live-verified registers (Compact P)

| Function | Register | Notes |
|---|---|---|
| Room current | 20286 | Extract / room air. Do **not** use 20260 as current (~5 C wrong on installs like issue #19) |
| Room setpoint | 20102 | Live-verified |
| DHW | 20460 | |
| Outdoor | 20282 | Scale 0.1 |
| Supply | 20284 | Scale 0.1 |
| Extract | 20286 | Scale 0.1 |
| Humidity | 20164 | No 0.1 scale |
| Fan speed | 21771 | Percent 0-100 on Compact P (integration maps to climate levels 0-4) |
| After heat exchange | 20288 | |
| After heat pump | 20290 | |

Protocol PDF (2018):  
https://www.en.nilan.dk/Files/Files/Engelsk/Downloads/7.%20Modbus%20-%20BACnet/2018_04_Modbus_CTS700_Modbus_protokol.pdf

## Live HA verification (04/08/2026)

Side-install from this fork `master` on Home Assistant OS, CTS700 Compact P over Modbus TCP (unit id 1, port 502). Existing Modbus YAML was paused for the test so only one poller ran.

| Check | Result |
|---|---|
| Room climate | Current ~24.5 C, setpoint 18 C |
| Humidity | 39% |
| DHW | Tank ~52 C |
| Outdoor / T1 | ~15.9 C |
| Fan (21771) | 75% (maps to climate fan level 3) |
| Config flow | TCP → CTS700 → create entry OK |

After the test, the Nilan config entry was removed and Modbus YAML restored as primary. Do not run YAML Modbus and this integration against the same unit at once.

Fixes from that pass (v1.3.1): climate HVAC mode no longer stuck on `unknown` for unmapped operating-mode values; fan percent mapped to levels 0-4 for the climate entity.

## MVP entities

- Room climate (current, setpoint, fan, on/off / mode where mapped)
- Outdoor, supply, extract, after HEX / HP, evaporator temps
- Humidity
- DHW setpoint and tank temperatures
- Days to air filter change

## Caveats

- Slave 4 floor / GEO-style maps often unavailable on Compact P Air-only installs
- CO2 reads 0 without a CO2 module: hide unused entities
- Avoid multiple Home Assistant pollers against the same CTS700
- PDF labels can differ from live Compact P setpoints
- Operating mode register `20120` is not a full CTS602-style heat/cool/auto enum on every Compact P; UI may show Auto when the raw value is unmapped

## Not this guide

If your Compact P uses a **CTS602** HMI / board (type id 44), use [../cts602/compactp.md](../cts602/compactp.md) instead.

## Related

- [CTS700 overview](README.md)
- [Hardware](../hardware.md)
- [FAQ](../faq.md)
- Issue tracking: https://github.com/veista/nilan/issues/19
