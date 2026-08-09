[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

# Nilan

Modbus TCP/RTU integration for Nilan ventilation and Compact units in Home Assistant.

[Docs](docs/README.md) · [Changelog](changelog/README.md) · [Installation](docs/installation.md) · [Dashboards](docs/dashboards.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Accessibility](ACCESSIBILITY.md) · [Code of Conduct](CODE_OF_CONDUCT.md) · [License](LICENSE)

## Vision (this fork)

Ship CTS700 Compact P eras (2015 / Nordic XL / 2018+) beside stable CTS602, document the full [nilan.no/produkter](https://www.nilan.no/produkter) catalog (bolig + næring) via coverage matrices, fix community CTS602 bugs, and keep shared Lovelace **Nilan-only**. GEO / slave 4 and CTS400 stay dump-gated until maps exist.

## Quick start

1. Install via [HACS](docs/installation.md) (default upstream, or this fork as a custom repository while testing).
2. Add **Nilan** → **TCP** or **Serial** → **Auto-detect** (or choose **CTS602** / **CTS700 2018+** / **CTS700 Nordic XL** / **CTS700 2015** manually).
3. Confirm the detected board and unit id, or override manually.
4. Typical unit ids: CTS602 **30**, Compact P CTS700 **1** (TCP port **502**).

**Is my model supported?** See the catalog matrices:

- [Bolig matrix](docs/catalog/bolig-matrix.md)
- [Næring matrix](docs/catalog/naering-matrix.md)
- [Marketing aliases](docs/catalog/aliases.md)
- [Compact P XL Nordic hub](docs/catalog/compact-p-xl-nordic.md)

**CTS700 maps:** era matrix in [cts700 README](docs/cts700/README.md). **2018+** 20xxx ([compact-p](docs/cts700/compact-p.md)), **Nordic XL** hybrid ([compact-p-nordic-xl](docs/cts700/compact-p-nordic-xl.md)), **2015** under 10000 ([legacy-2015](docs/cts700/legacy-2015.md)). Per-board Modbus YAML: [`modbus_yaml/`](modbus_yaml/). **Compact P2** prefers CTS602 ([compact-p2](docs/cts602/compact-p2.md)).

### Install from this fork (HACS custom repository)

Until CTS700 and related fixes are merged upstream:

1. HACS → three-dot menu → **Custom repositories**
2. URL: `https://github.com/master3395/veista-nilan`
3. Category: **Integration**
4. Download **Nilan** → restart Home Assistant
5. If you already had veista/nilan installed, remove the old integration entry first (same domain)

Fork: https://github.com/master3395/veista-nilan (`master`)

## Controllers

| Controller | Status | Overview |
|---|---|---|
| CTS602 | Stable | [docs/cts602](docs/cts602/README.md) |
| CTS700 | MVP | [docs/cts700](docs/cts700/README.md) |
| CTS400 | Not implemented | [docs/naering/cts400.md](docs/naering/cts400.md) |

Catalog: [docs/catalog](docs/catalog/bolig-matrix.md) · Commercial research: [docs/naering](docs/naering/README.md)

Shared: [Hardware](docs/hardware.md) · [Installation](docs/installation.md) · [Dashboards](docs/dashboards.md) · [FAQ](docs/faq.md)

## CTS602 models

| Model | Type id | Guide |
|---|---|---|
| Comfort light | 2 | [comfort-light](docs/cts602/comfort-light.md) |
| Comfort Polar | 3 | [comfort-polar](docs/cts602/comfort-polar.md) |
| VPL 15c | 4 | [vpl-15c](docs/cts602/vpl-15c.md) |
| CompactS | 10 | [compacts](docs/cts602/compacts.md) |
| VP 18comp | 11 | [vp-18comp](docs/cts602/vp-18comp.md) |
| VP18cCom | 12 | [vp18ccom](docs/cts602/vp18ccom.md) |
| COMFORT | 13 | [comfort](docs/cts602/comfort.md) |
| VP 18c | 19 | [vp-18c](docs/cts602/vp-18c.md) |
| VP 18ek | 20 | [vp-18ek](docs/cts602/vp-18ek.md) |
| VP 18cek | 21 | [vp-18cek](docs/cts602/vp-18cek.md) |
| VPL 25c | 25 | [vpl-25c](docs/cts602/vpl-25c.md) |
| VPM/28EC | 26 | [vpm-28ec](docs/cts602/vpm-28ec.md) |
| VP18cCoB | 28 | [vp18ccob](docs/cts602/vp18ccob.md) |
| COMPACTn | 30 | [compactn](docs/cts602/compactn.md) |
| COMFORTn | 31 | [comfortn](docs/cts602/comfortn.md) |
| VP18 M2 | 32 | [vp18-m2](docs/cts602/vp18-m2.md) |
| COMBI 300 N | 33 | [combi-300-n](docs/cts602/combi-300-n.md) |
| COMBI 302 | 35 | [combi-302](docs/cts602/combi-302.md) |
| COMBI 302 T | 36 | [combi-302-t](docs/cts602/combi-302-t.md) |
| VGU180 ek | 38 | [vgu180-ek](docs/cts602/vgu180-ek.md) |
| VENTEC | 42 | [ventec](docs/cts602/ventec.md) |
| CompactP (AIR/GEO) | 44 | [compactp](docs/cts602/compactp.md) · [compact-p2](docs/cts602/compact-p2.md) |

## CTS700 models

| Model / map | Guide |
|---|---|
| Compact P (2018+ Ethernet map) | [compact-p](docs/cts700/compact-p.md) |
| Compact P Nordic XL (hybrid) | [compact-p-nordic-xl](docs/cts700/compact-p-nordic-xl.md) |
| CTS700 2015 legacy map | [legacy-2015](docs/cts700/legacy-2015.md) |
| GEO / slave 4 | [geo](docs/cts700/geo.md) (dump-gated) |

MVP covers room climate, fan, temps, humidity, and DHW setpoint. Not full CTS700 family support yet. On 2018+ Compact P, do not use register **20260** as room current; keep fan on **21771** (never Nordic **4747** steps). Tracking: [veista/nilan#19](https://github.com/veista/nilan/issues/19).

Full SKU coverage: [docs/catalog/bolig-matrix.md](docs/catalog/bolig-matrix.md) · [docs/catalog/naering-matrix.md](docs/catalog/naering-matrix.md).

## Support

If you like the integration, please leave a star and consider donating or becoming a sponsor.
