# Compact P XL Nordic (catalog hub)

Nilan marketing: [Compact P XL Nordic](https://www.nilan.no/produkter/ventilasjon-med-oppvarming/ventilasjon-og-varmtvann/compact-p-xl-nordic).

## Which board?

| Evidence on your unit | Choose in HA |
|---|---|
| CTS602 HMI / type id **44**, typical unit id **30**, RS485 | **CTS602** → [../cts602/compactp.md](../cts602/compactp.md) |
| Holding **4747** in **101–104** (Nordic step fan) | **CTS700 Compact P Nordic XL** → [../cts700/compact-p-nordic-xl.md](../cts700/compact-p-nordic-xl.md) |
| Fan **21771** percent, setpoint **20102**, room **20286** | **CTS700 (2018+)** → [../cts700/compact-p.md](../cts700/compact-p.md) |
| Classic under-10000 percent fan on **4747** (not 101–104) | **CTS700 (2015 legacy)** → [../cts700/legacy-2015.md](../cts700/legacy-2015.md) |

Prefer **Auto-detect** when unsure. Probe order: CTS602 → Nordic → 2018+ → 2015.

## Do not mix

- One `board_type` per config entry
- One Modbus poller per unit (integration **or** YAML, not both)
- Do not load two `modbus_yaml/` files for the same host

## Aliases

Python aliases include Compact P XL Nordic, Nordic XL RF, and related plate text. See [aliases.md](aliases.md).
