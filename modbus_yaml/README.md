# Per-board Modbus YAML (2015 and up)

Reference / fallback Home Assistant **Modbus** YAML aligned with this fork’s Python maps. **Not** one file for every board: fan encodings differ.

## Pick one file

| File | Board | Use when |
|---|---|---|
| [`cts700_2015_legacy.yaml`](cts700_2015_legacy.yaml) | `CTS700_LEGACY` | Fan **4747** percent; classic under-10000 map |
| [`cts700_nordic_xl.yaml`](cts700_nordic_xl.yaml) | `CTS700_NORDIC` | Fan **4747** = **101–104**; mark007 parity |
| [`cts700_2018_compact_p.yaml`](cts700_2018_compact_p.yaml) | `CTS700` | Fan **21771**; setpoint **20102**; room **20286** |
| [`cts602_compactp.yaml`](cts602_compactp.yaml) | `CTS602` CompactP (44) | Catalog Compact P XL Nordic / type 44 RS485 (unit 30) |

## Rules

1. Replace `YOUR_HOST_IP` (and unit id if needed) before use.
2. Load **only one** of these files for a given unit.
3. Do **not** run YAML Modbus and the **Nilan** custom integration against the same unit at once.
4. Prefer the Nilan board menu / Auto-detect in production; YAML is for bring-up or comparison.
5. Keep YAML in sync with the matching Python register map when you change entities.

## Era docs

- [CTS700 era matrix](../docs/cts700/README.md)
- [Catalog Compact P XL Nordic hub](../docs/catalog/compact-p-xl-nordic.md)
