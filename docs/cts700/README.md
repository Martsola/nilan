# CTS700

MVP / experimental support for Nilan **CTS700** controllers.

## Current scope

- Primary target: **Compact P** over Ethernet Modbus TCP
- Indoor unit id: typically **1**
- Port: **502**
- Native LAN: Cat5e (or better) from CTS700 LAN to router; no RS485 bridge required

## Device guides

| Model | Guide |
|---|---|
| Compact P | [compact-p.md](compact-p.md) |

## Status

MVP live-checked on Compact P Ethernet (04/08/2026). Details and register notes: [compact-p.md](compact-p.md). Current integration version: **1.3.1**.

## Out of MVP (for now)

- Old CTS700 firmware maps (registers under 10000)
- Full GEO / floor slave 4 feature set
- Full feature parity with CTS602 (alarms, week programs, all selects)

Help wanted: register dumps and entity pass/fail reports. See [CONTRIBUTING.md](../../CONTRIBUTING.md) and issue [#19](https://github.com/veista/nilan/issues/19).
