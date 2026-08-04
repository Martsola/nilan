[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
# Nilan

Modbus TCP/RTU integration for Nilan ventilation and Compact units in Home Assistant.

## Supported controllers

### CTS602

Supported devices (as typed in HMI menu):

- Comfort light
- Comfort Polar
- VPL 15c
- CompactS
- VP18cCom
- COMFORT
- VP 18c
- VP 18ek
- VP 18cek
- VPL 25c
- VPM/28EC
- VP18cCoB
- COMPACTn
- COMFORTn
- COMBI 300 N
- COMBI 302
- COMBI 302 T
- VGU180 ek
- VENTEC
- CompactP (AIR/GEO)

Majority of functions are supported. If some critical feature is missing, please leave an issue.

### CTS700 (MVP)

Experimental community-tested support for **Compact P** over **Ethernet Modbus TCP** (indoor mostly slave / unit id **1**).

Included in the MVP: room climate (current + setpoint), fan speed, outdoor / supply / extract temps, humidity, DHW setpoint and tank temps, filter days.

Not full CTS700 family support yet: old firmware maps (registers under 10000), GEO / slave 4 floor maps, and full CTS602 feature parity are out of scope for this MVP. Hide unused entities in the UI when a register is unavailable on your unit.

## Hardware

You must have one interface type available on your Nilan device for this integration to work.

### CTS700 Ethernet (native LAN)

Cat5e (or better) from the CTS700 LAN port to your router is enough for Modbus TCP. No RS485 bridge is required for native Ethernet CTS700.

- TCP port: **502**
- Typical indoor unit id: **1**
- Example host only: `192.168.1.50` (do not publish real LAN IPs in issues)

### CTS602-style and RTU installs

Supported interface types:

- ModBus RTU to Modbus TCP Bridge
- USB to RS485 adaptor

#### Tested known-to-work bridge devices

* USR-TCP232-410S
* Waveshare RS485 TO ETH (B)
* https://github.com/veista/modbus_bridge

## Installation

### Manually

- Copy the `nilan` folder into your `custom_components` folder
- Restart HA
- Add Nilan from Integrations
- Choose interface (TCP / Serial), then board type (**CTS602** or **CTS700**)
- For Compact P CTS700, use unit id **1** and port **502**

### HACS

- This integration is available from HACS
- Add Nilan from Integrations

### Fork testing (CTS700 MVP)

While validating Compact P support, you can install from the working fork branch:

- Repository: https://github.com/master3395/veista-nilan
- Branch: `cts700-compact-p-mvp`
- Copy `custom_components/nilan` from that branch, or add the fork as a custom HACS repository during testing

## CTS700 setup notes

| Function | Register | Notes |
|---|---|---|
| Room current | 20286 | Extract / room air. Do **not** use 20260 as current (~5 C wrong on Compact P installs like issue #19) |
| Room setpoint | 20102 | Live-verified on Compact P |
| DHW | 20460 | |
| Outdoor | 20282 | Scale 0.1 |
| Supply | 20284 | Scale 0.1 |
| Extract | 20286 | Scale 0.1 |
| Humidity | 20164 | No 0.1 scale |
| Fan speed | 21771 | |
| After heat exchange | 20288 | |
| After heat pump | 20290 | |

Protocol PDF (2018):  
https://www.en.nilan.dk/Files/Files/Engelsk/Downloads/7.%20Modbus%20-%20BACnet/2018_04_Modbus_CTS700_Modbus_protokol.pdf

Caveats:

- Slave 4 floor / GEO-style maps are often unavailable on Compact P Air-only installs
- CO2 reads 0 without a CO2 module
- CTS700 can struggle with multiple Home Assistant pollers; keep polling conservative
- PDF labels can differ from live Compact P setpoints (`20102` vs older PDF names)

Tracking issue: https://github.com/veista/nilan/issues/19

## FAQ

**CTS602 vs CTS700?** Different register maps and typical unit ids (CTS602 often 30; Compact P CTS700 indoor often 1).

**Why does the PDF disagree with live values?** Firmware eras and Compact P mappings differ. Prefer live-verified registers above for Compact P Ethernet.

## Issues

1. Before submitting an issue, read the previous <a href="https://github.com/veista/nilan/issues?q=">issues</a>, <a href="https://github.com/veista/nilan/wiki">wiki</a>, <a href="https://github.com/veista/nilan/discussions">discussions</a> and <a href="https://github.com/veista/nilan/releases">release notes</a>.
2. CTS700 Compact P MVP is developed on the fork first. Still need dumps for GEO / slave 4 and old firmware (&lt;10000). Please include: device plate photo, firmware version, slave map, register dump, and which entities work or fail.
3. If you have a CTS602 device and you get a device not supported error during installation:
  - Turn on debug logging for the integration and try installing the integration again. Take note of the debug log and submit it with the issue.
  - Take a picture of the device type plate and submit it with the issue.
  - If you have HMI350T - Touch screen HMI - installed on your device, take a picture of the device info page and submit it with the issue.
  - If you have CTS602 HMI, take a picture of "SHOW DATA" -> "TYPE" and submit it with the issue.
4. On other Issues:
  - Submit the following: Logs, Modbus Version, Device Type - as Shown in the Integration, Device Version - as Shown in the Integration

## Support

If you like the integration, please leave a star and consider donating or becoming a sponsor.
