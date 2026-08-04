[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

# Nilan

Modbus TCP/RTU integration for Nilan ventilation and Compact units in Home Assistant.

[Docs](docs/README.md) · [Contributing](CONTRIBUTING.md) · [License](LICENSE)

## Quick start

1. Install via [HACS](docs/installation.md) or copy `custom_components/nilan` into Home Assistant.
2. Add **Nilan** → **TCP** or **Serial** → board **CTS602** or **CTS700**.
3. Set unit id: CTS602 often **30**, Compact P CTS700 often **1** (port **502**).

Fork for CTS700 work: https://github.com/master3395/veista-nilan (`master`)

## Controllers

| Controller | Status | Overview |
|---|---|---|
| CTS602 | Stable | [docs/cts602](docs/cts602/README.md) |
| CTS700 | MVP | [docs/cts700](docs/cts700/README.md) |

Shared: [Hardware](docs/hardware.md) · [Installation](docs/installation.md) · [FAQ](docs/faq.md)

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
| COMBI 300 N | 33 | [combi-300-n](docs/cts602/combi-300-n.md) |
| COMBI 302 | 35 | [combi-302](docs/cts602/combi-302.md) |
| COMBI 302 T | 36 | [combi-302-t](docs/cts602/combi-302-t.md) |
| VGU180 ek | 38 | [vgu180-ek](docs/cts602/vgu180-ek.md) |
| VENTEC | 42 | [ventec](docs/cts602/ventec.md) |
| CompactP (AIR/GEO) | 44 | [compactp](docs/cts602/compactp.md) |

## CTS700 models

| Model | Guide |
|---|---|
| Compact P (Ethernet Modbus TCP) | [compact-p](docs/cts700/compact-p.md) |

MVP covers room climate, fan, temps, humidity, and DHW. Not full CTS700 family support yet. Do not use register **20260** as room current on Compact P. Details: [Compact P guide](docs/cts700/compact-p.md). Tracking: [veista/nilan#19](https://github.com/veista/nilan/issues/19).

## Support

If you like the integration, please leave a star and consider donating or becoming a sponsor.
