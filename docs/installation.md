# Installation

## HACS

1. Install **Nilan** from HACS (default repository for the upstream release).
2. Restart Home Assistant.
3. Settings → Devices & services → Add integration → **Nilan**.
4. Choose **TCP** or **Serial**.
5. Choose board type: **CTS602** or **CTS700 (Compact P MVP)**.
6. Enter host, port, and unit id (see device docs).

## Manual

1. Copy `custom_components/nilan` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the integration as above.

## Fork testing (CTS700 MVP)

While validating Compact P support on this fork:

- Repository: https://github.com/master3395/veista-nilan
- Branch: `cts700-compact-p-mvp`
- Copy `custom_components/nilan` from that branch, or add the fork as a custom HACS repository during testing

## Defaults

| Board | Port | Unit id |
|---|---|---|
| CTS602 | 502 (TCP) | 30 |
| CTS700 Compact P | 502 | 1 |

See [hardware.md](hardware.md) and the guide for your model under [README.md](README.md).
