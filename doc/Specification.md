# TEST6967 Specification

| Item | Value |
| --- | --- |
| Process | IHP SG13CMOS5L (ihp-sg13cmos5l PDK, IHP-Open-PDK dev `c6562037497437ce6bc689e633e5b45abf9bbccb`) |
| Die size (seal ring) | 1000 x 1000 um |
| Top cell | TEST6967 |
| Devices | none (purely passive: metal lines, pads, ground) |
| Metal stack used | Metal1 ... TopMetal1, passivation openings on the pads |
| Supply / bias | none |
| Test structures | RF_PROBE with on-chip TopMetal1 network to RF_BOND_A and RF_BOND_B; CAL_OPEN, CAL_SHORT, CAL_LINE150 |
| Probe pads | GSG, 100-um pitch, TopMetal1, probed from the left (-x) |
| Frequency range | D-band, centre 130 GHz |
| Fill | PDK filler (Activ, GatPoly, Metal1 ... Metal4); no fill on TopMetal1 and in the RF structures |

Pads: [Datasheet.md](./Datasheet.md). Sign-off: [../release/v.1.0.0/doc/Signoff.md](../release/v.1.0.0/doc/Signoff.md).
