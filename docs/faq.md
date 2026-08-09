# FAQ

## CTS602 vs CTS700?

Different controller boards, register maps, and typical unit ids.

- CTS602: often unit id **30**, RTU bridge or serial common
- CTS700 Compact P: often unit id **1**, native Ethernet Modbus TCP on port **502**

## Can the integration auto-detect my board?

Yes. After TCP or Serial, choose **Auto-detect**. Probe order: CTS602 `control_type` (1000), then CTS700 Nordic (holding **4747** in **101–104**), then CTS700 2018+ outdoor temp (20282), then CTS700 2015 T1+setpoint (5152 / 4746). Unit id **1** then **30** if you leave unit id empty. Confirm the result before the entry is created. You can still pick CTS602, CTS700 Nordic XL, CTS700 2018+, or CTS700 2015 manually.

## Why can the CTS700 PDF disagree with live values?

Firmware eras differ:

- **2015 map** (PDF 20150826): registers mostly under 10000 (setpoint 4746, fan **4747 percent**, …). Use board **CTS700 (2015 legacy map)**. Guide: [cts700/legacy-2015.md](cts700/legacy-2015.md).
- **Nordic XL hybrid**: fan **4747 = 101–104**, mixed classic + 20xxx. Use **CTS700 Compact P Nordic XL**. Guide: [cts700/compact-p-nordic-xl.md](cts700/compact-p-nordic-xl.md).
- **2018+ / Compact P map**: 20xxx registers (fan **21771** percent, setpoint **20102**). Use board **CTS700 (2018+ / Compact P)**. Guide: [cts700/compact-p.md](cts700/compact-p.md).

Compact P live installs may also disagree with some PDF labels. Prefer live-verified tables in those guides. Era matrix: [cts700/README.md](cts700/README.md).

## Compact P XL Nordic: CTS602 or CTS700?

Catalog pages often say CTS602. If HMI type is **44** / unit id **30**, choose **CTS602**. If Modbus shows Nordic step fan on **4747**, choose **CTS700 Compact P Nordic XL**. Hub: [catalog/compact-p-xl-nordic.md](catalog/compact-p-xl-nordic.md).

## Unsupported device on CTS602?

Confirm the HMI type string / type id against [cts602/README.md](cts602/README.md). Attach debug logs and plate photos as described in [CONTRIBUTING.md](../CONTRIBUTING.md). Type **32** (VP18 M2) is included on this fork; see [vp18-m2.md](cts602/vp18-m2.md).

## CO2 always 0?

No CO2 module installed, or the entity is not applicable. Hide the entity in the UI. On older Modbus versions the integration now probes CO2 presence instead of requiring bus version 10 or higher.

## Norwegian language (bokmål) missing strings?

Use Home Assistant language **Norsk bokmål** (`nb`). This fork ships `translations/nb.json` (renamed from `no.json`).

## Slave 4 / floor / GEO missing on Compact P?

Often unavailable on Air-only Compact P installs. Documented as dump-gated: [cts700/geo.md](cts700/geo.md).

## Compact P2: CTS602 or CTS700?

Current Nilan Compact P2 manuals list **CTS602**. Use board **CTS602** (unit id 30). See [cts602/compact-p2.md](cts602/compact-p2.md). Only use CTS700 if a dump shows 20xxx Ethernet registers.

## Commercial Comfort 600 / VPM / VR / VPR?

Product pages and gateway docs point to **CTS602** Modbus RS485 (default unit id 30). Choose **CTS602** or Auto-detect. If the HMI type id is unknown to the integration, share a dump. Full list: [catalog/naering-matrix.md](catalog/naering-matrix.md). Do not pick CTS700 Compact P maps for commercial units unless proven.

## Where are the dashboards?

Optional Nilan-only Lovelace YAML lives under [`dashboards/`](../dashboards/). See [dashboards.md](dashboards.md). They are not auto-installed by HACS.
