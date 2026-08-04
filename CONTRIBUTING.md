# Contributing

Thank you for helping improve the Nilan Home Assistant integration.

## Branch targets (this fork)

Working fork: https://github.com/master3395/veista-nilan

- Day-to-day CTS700 Compact P work lives on fork **`master`**
- Upstream project: https://github.com/veista/nilan
- Open a pull request to `veista/nilan` only when the change is ready and tested

Do not open drive-by PRs against unrelated branches.

## Before you open an issue

1. Read previous [issues](https://github.com/veista/nilan/issues), [wiki](https://github.com/veista/nilan/wiki), [discussions](https://github.com/veista/nilan/discussions), and [release notes](https://github.com/veista/nilan/releases).
2. Check device docs under [`docs/`](docs/README.md) for your controller and model.

## Reporting CTS700 issues

CTS700 Compact P MVP is developed on this fork first. Still needed: GEO / slave 4 dumps and old firmware maps (registers under 10000).

Please include:

- Device plate photo
- Firmware / software version
- Slave / unit id map
- Register dump (or Modbus YAML) for the registers you care about
- Which entities work or fail
- Example host only in public posts: `192.168.1.50` (never paste real LAN IPs)

Tracking: https://github.com/veista/nilan/issues/19

## Reporting CTS602 issues

If install fails with unsupported device:

1. Enable debug logging for the integration and try again; attach the log.
2. Photo of the device type plate.
3. HMI350T: photo of the device info page.
4. CTS602 HMI: photo of `SHOW DATA` -> `TYPE`.

For other bugs, include: logs, Modbus version, device type and device version as shown in the integration.

## Pull requests

1. Fork and create a topic branch from the branch you intend to improve.
2. Keep CTS602 behavior unchanged unless the PR is explicitly about CTS602.
3. Prefer small, focused commits with a clear why.
4. Update [`docs/`](docs/README.md) when you add or change device support.
5. Do not put secrets, real LAN IPs, or credentials in commits or issue text.
6. Do not use em dash characters (Unicode U+2014) in user-facing docs or README copy for this fork.

## Code notes

- Secrets belong in Home Assistant config / secrets, never in this repository.
- CTS602 and CTS700 use different register maps and typical unit ids.
- Keep modules readable; large device I/O belongs in dedicated modules (for example `device_cts700.py`).

## License

By contributing, you agree that your contributions are licensed under the same [Apache License 2.0](LICENSE) as the project.
