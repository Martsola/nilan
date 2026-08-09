# Compact P Nordic XL (CTS700 hybrid)

Community-proven **CTS700** hybrid map for Compact P Nordic XL / Nordic XL RF units that answer classic addresses plus some 20xxx holdings. Fan user step is **4747 = 101–104**, not percent.

Catalog product page often lists **CTS602** for Compact P XL Nordic. If your unit is RS485 / HMI type 44, use [../cts602/compactp.md](../cts602/compactp.md) instead. If Modbus shows Nordic step fan on 4747, use this board.

## When to use

Choose **CTS700 Compact P Nordic XL** in the config flow, or Auto-detect when holding **4747** is in **101–104**.

Use this if:

- Fan writes as steps **101–104** on register **4747**
- Room setpoint is **4746**, room current is input **5154**
- Live humidity on input **4716**, average humidity on **20164**

Do **not** use this map on 2018+ Compact P units that use fan **21771** percent and setpoint **20102**. That path is [compact-p.md](compact-p.md).

## Connection defaults

| Setting | Value |
|---|---|
| Protocol | Modbus TCP (or Serial) |
| Port | **502** (TCP) |
| Unit id | often **1** |

## Registers (full parity)

| Function | Register | Notes |
|---|---|---|
| Room setpoint | 4746 holding | Scale 0.1 |
| Fan step | 4747 holding | **101–104** = steps 1–4 |
| Live humidity | 4716 input | 0–100 |
| Average humidity | 20164 holding | 0–100 |
| T1 outdoor | 5152 input | Scale 0.1 |
| T2 supply | 5153 input | Scale 0.1 |
| T3 extract / room | 5154 input | Scale 0.1 |
| T8 preheater | 5159 input | Scale 0.1 |
| T11 / T12 DHW | 5162 / 5163 input | Scale 0.1 |
| Filter alarm | 5168 input | Binary |
| Filter days | 20103 holding | |
| Op mode | 5432 holding | 0 off, 1 cool, 2 heat, 3 dehum, 4 DHW |
| Anode | 4233 holding | |
| Fan power % | 21771 holding | Readout; climate fan writes use 4747 steps |
| Supply / extract fan % | 4699 / 4700 | |
| T4 / T5 / T6 | 20288 / 20290 / 20292 | |
| DHW setpoint | 20460 | |

External CO2 is out of bus scope for this map.

## Caveats

- **Week programs** are not synced by this integration. Changing climate fan/setpoint from Home Assistant can disagree with a week program still active on the controller. Prefer disabling conflicting week slots while testing.
- Do **not** run native Modbus YAML and the Nilan integration against the same unit at once.
- Never copy Nordic step fan writes onto a 2018+ Compact P entry.

## Related

- [CTS700 era matrix](README.md)
- [2018+ Compact P](compact-p.md)
- [2015 legacy](legacy-2015.md)
- [CTS602 CompactP](../cts602/compactp.md)
- Reference YAML: [`modbus_yaml/cts700_nordic_xl.yaml`](../../modbus_yaml/cts700_nordic_xl.yaml)
- Dashboard: [`dashboards/cts700_compact_p_nordic_xl.yaml`](../../dashboards/cts700_compact_p_nordic_xl.yaml)
