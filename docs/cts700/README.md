# CTS700

Support for Nilan **CTS700** controllers over Modbus (Ethernet TCP or Serial).

## Maps

| Map | Board choice in HA | Typical registers | Guide |
|---|---|---|---|
| **2018+** Compact P | CTS700 (2018+ / Compact P) | 20xxx (e.g. 20102, 20282, 21771) | [compact-p.md](compact-p.md) |
| **2015** legacy | CTS700 (2015 legacy map) | under 10000 (e.g. 4746, 5152, 5548) | [legacy-2015.md](legacy-2015.md) |

Auto-detect probes CTS602, then 2018+ CTS700, then 2015 CTS700.

## Connection defaults

- Indoor unit id: typically **1**
- TCP port: **502**
- Native LAN: Cat5e (or better) from CTS700 LAN to router; no RS485 bridge required for Ethernet

## Status

- **2018+ Compact P:** live-checked (04/08/2026). See [compact-p.md](compact-p.md).
- **2015 legacy:** MVP from the 20150826 PDF; needs community dumps to refine sensor naming and DHW tank currents.

Current integration version: **1.3.4**.

## Still out of scope

- Full GEO / floor slave 4 feature set ([geo.md](geo.md))
- Full feature parity with CTS602 (alarms, week programs, all selects)
- Installer auth at register 7777

Help wanted: register dumps and entity pass/fail reports. See [CONTRIBUTING.md](../../CONTRIBUTING.md) and issue [#19](https://github.com/veista/nilan/issues/19).
