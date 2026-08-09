# Lovelace dashboards (Nilan only)

These examples live in [`dashboards/`](../dashboards/) and contain **only Nilan** cards and entities. They are not installed automatically by HACS.

## Before you import

1. Install and configure the Nilan integration.
2. Confirm entities exist under Settings → Devices → Nilan.
3. If your device name is not `Nilan`, search-replace `nilan_` in the YAML (HA entity ids follow the device name).

## Import (UI)

1. Settings → Dashboards → **Add dashboard**.
2. Open the new dashboard → three-dot menu → **Raw configuration editor**.
3. Paste the contents of:
   - [`dashboards/cts700_compact_p.yaml`](../dashboards/cts700_compact_p.yaml) for CTS700 Compact P 2018+,
   - [`dashboards/cts700_compact_p_nordic_xl.yaml`](../dashboards/cts700_compact_p_nordic_xl.yaml) for Nordic XL, or
   - [`dashboards/cts602_overview.yaml`](../dashboards/cts602_overview.yaml) for CTS602
4. Save. Fix any unknown entities (hide or remove cards your unit does not expose).

## Import (YAML mode)

Advanced users can include the view YAML under a Lovelace dashboard configuration. Prefer the UI raw editor if you use storage mode dashboards.

## Scope rules

- Nilan ventilation, DHW, filters, setpoints, and related integration entities only
- No energy tariffs, cameras, weather, or other house dashboards
- Stock Home Assistant cards only (no required custom HACS cards)
