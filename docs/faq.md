# FAQ

## CTS602 vs CTS700?

Different controller boards, register maps, and typical unit ids.

- CTS602: often unit id **30**, RTU bridge or serial common
- CTS700 Compact P: often unit id **1**, native Ethernet Modbus TCP on port **502**

## Can the integration auto-detect my board?

Yes. After TCP or Serial, choose **Auto-detect**. The flow probes CTS602 `control_type` (1000), then CTS700 outdoor temperature registers, using unit id **1** then **30** if you leave unit id empty. Confirm the result before the entry is created. You can still pick CTS602 or CTS700 manually.

## Why can the CTS700 PDF disagree with live values?

Firmware eras differ (old maps under 10000 vs newer 20xxx). Compact P live installs may also disagree with some PDF labels. Prefer live-verified registers in [cts700/compact-p.md](cts700/compact-p.md).

## Unsupported device on CTS602?

Confirm the HMI type string / type id against [cts602/README.md](cts602/README.md). Attach debug logs and plate photos as described in [CONTRIBUTING.md](../CONTRIBUTING.md). Type **32** (VP18 M2) is included on this fork; see [vp18-m2.md](cts602/vp18-m2.md).

## CO2 always 0?

No CO2 module installed, or the entity is not applicable. Hide the entity in the UI. On older Modbus versions the integration now probes CO2 presence instead of requiring bus version 10 or higher.

## Norwegian language (bokmål) missing strings?

Use Home Assistant language **Norsk bokmål** (`nb`). This fork ships `translations/nb.json` (renamed from `no.json`).

## Slave 4 / floor / GEO missing on Compact P?

Often unavailable on Air-only Compact P installs. Documented as out of CTS700 MVP scope until dumps exist.

## Where are the dashboards?

Optional Nilan-only Lovelace YAML lives under [`dashboards/`](../dashboards/). See [dashboards.md](dashboards.md). They are not auto-installed by HACS.
