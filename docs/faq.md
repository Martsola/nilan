# FAQ

## CTS602 vs CTS700?

Different controller boards, register maps, and typical unit ids.

- CTS602: often unit id **30**, RTU bridge or serial common
- CTS700 Compact P: often unit id **1**, native Ethernet Modbus TCP on port **502**

## Why can the CTS700 PDF disagree with live values?

Firmware eras differ (old maps under 10000 vs newer 20xxx). Compact P live installs may also disagree with some PDF labels. Prefer live-verified registers in [cts700/compact-p.md](cts700/compact-p.md).

## Unsupported device on CTS602?

Confirm the HMI type string / type id against [cts602/README.md](cts602/README.md). Attach debug logs and plate photos as described in [CONTRIBUTING.md](../CONTRIBUTING.md).

## CO2 always 0?

No CO2 module installed, or the entity is not applicable. Hide the entity in the UI.

## Slave 4 / floor / GEO missing on Compact P?

Often unavailable on Air-only Compact P installs. Documented as out of CTS700 MVP scope until dumps exist.
