[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

# Nilan

Modbus TCP/RTU integration for Nilan ventilation and Compact units in Home Assistant.

**Docs** · **[Contributing](CONTRIBUTING.md)** · **[License](LICENSE)**

> GitHub shows **README**, **Contributing**, and **License** tabs when those files exist at the repository root (same pattern as [cyberpanel `v2.5.5-dev`](https://github.com/master3395/cyberpanel/tree/v2.5.5-dev)).

---

## Supported controllers

| Controller | Status | Start here |
|---|---|---|
| **CTS602** | Stable | [docs/cts602](docs/cts602/README.md) |
| **CTS700** | MVP (Compact P Ethernet) | [docs/cts700](docs/cts700/README.md) |

Full per-device guides: **[docs/README.md](docs/README.md)**

### CTS602 (HMI names)

Comfort light, Comfort Polar, VPL 15c, CompactS, VP18cCom, COMFORT, VP 18c, VP 18ek, VP 18cek, VPL 25c, VPM/28EC, VP18cCoB, COMPACTn, COMFORTn, COMBI 300 N, COMBI 302, COMBI 302 T, VGU180 ek, VENTEC, CompactP (AIR/GEO).

### CTS700 (MVP)

Compact P over Ethernet Modbus TCP (unit id **1**, port **502**). Room climate, fan, temps, humidity, DHW. Not full CTS700 family coverage yet.

---

## Quick start

1. Install via [HACS](docs/installation.md) or copy `custom_components/nilan`.
2. Add **Nilan** → TCP or Serial → **CTS602** or **CTS700**.
3. Confirm unit id (CTS602 often **30**, Compact P CTS700 often **1**).

Hardware details: [docs/hardware.md](docs/hardware.md)

### Fork testing (CTS700)

- https://github.com/master3395/veista-nilan branch `cts700-compact-p-mvp`

---

## Documentation map

| Topic | Link |
|---|---|
| All devices | [docs/README.md](docs/README.md) |
| Hardware | [docs/hardware.md](docs/hardware.md) |
| Installation | [docs/installation.md](docs/installation.md) |
| FAQ | [docs/faq.md](docs/faq.md) |
| Compact P CTS700 | [docs/cts700/compact-p.md](docs/cts700/compact-p.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| License | [LICENSE](LICENSE) |

CTS700 register notes and caveats live in the Compact P guide (do not use register **20260** as room current on Compact P).

Tracking: https://github.com/veista/nilan/issues/19

---

## Support

If you like the integration, please leave a star and consider donating or becoming a sponsor.
