# TEST6967 Datasheet

Purely passive 130-GHz test chip, 1000 x 1000 um, IHP SG13CMOS5L. No supply and no bias; all structures are
measured with RF probes.

## Structures

| Structure | Description |
|---|---|
| RF_PROBE | GSG probe pad, 100-um pitch, at x = 634.82 um, y = 500 um, probed from the left (-x); Metal2 shield below the signal pad, tied to the ground pads |
| On-chip network | TopMetal1 lines over Metal1 ground from RF_PROBE to RF_BOND_A and RF_BOND_B |
| RF_BOND_A, RF_BOND_B | RF pads at the right chip edge, each with two ground pads |
| CAL_OPEN | GSG pad in the ground plate, open (same pad geometry, Metal2 shield and ground window as RF_PROBE) |
| CAL_SHORT | GSG pad in the ground plate, short at the window edge (same pad geometry, Metal2 shield and ground window as RF_PROBE) |
| PROBE_TEST | GSG pad between CAL_OPEN and CAL_SHORT, shorted like CAL_SHORT, for probe landing and contact tests; uses their neighbouring ground pads |
| LAND_A, LAND_B | floating TopMetal1 pads at the left chip edge, mirror image of the RF pads in x, as landing pads for wires from a neighbouring chip |
| GND_DC | two ground pads (top and bottom) |
| Ground | TopMetal1 plate with slits from x = 345 um to the right chip edge, Metal1 grid below (not below the Metal2 pad shields), via stacks Metal1 to TopMetal1 on a 40-um grid; LAND_A, LAND_B and PDK filler left of the plate |

## Pads

Chip coordinates in um, origin at the lower left corner of the die (seal ring included). Centre and size are
those of the passivation opening.

| Pad | Centre | Passivation opening |
|---|---|---|
| RF_PROBE (S) | (634.82, 500.00) | 55.8 x 35.8 |
| RF_PROBE GND (2x) | (634.82, 400.00), (634.82, 600.00) | 55.8 x 75.8 |
| CAL_OPEN (S) | (430.00, 300.00) | 55.8 x 35.8 |
| CAL_SHORT (S) | (430.00, 700.00) | 55.8 x 35.8 |
| PROBE_TEST (S) | (430.00, 500.00) | 55.8 x 35.8 |
| CAL GND (4x) | (430.00, 200 / 400 / 600 / 800) | 55.8 x 75.8 |
| RF_BOND_A (S) | (895.82, 792.00) | 65.0 x 65.0 |
| RF_BOND_B (S) | (895.82, 208.00) | 65.0 x 65.0 |
| LAND_A | (104.18, 792.00) | 65.0 x 65.0 |
| LAND_B | (104.18, 208.00) | 65.0 x 65.0 |
| RF_BOND GND (4x) | (900.82, 101.5 / 314.5 / 685.5 / 898.5) | 55.0 x 42.0 |
| GND_DC (2x) | (510.00, 105.00), (510.00, 895.00) | 75.8 x 75.8 |

Pin labels are on TopMetal1 pin (126/25).

![Layout](TEST6967.png)
