# TEST6967 v.1.0.0

First release. `gds/TEST6967.gds` is the GDS for submission (seal ring and filler included, checksum in
`gds/SHA256SUMS`), top cell `TEST6967`, saved with the KLayout options required by Open-Silicon-MPW (no PCell
context, zero-length paths eliminated, max. 8000 vertices, library name LIB, database unit 0.001 um).

- Seal ring: ihp-sg13cmos5l PCell at IHP-Open-PDK dev `c6562037`, 1000 x 1000 um. Its area label is
  `1.0 sq mm` (the PCell writes `1.0e-06 sq mm`).
- Fill: ihp-sg13cmos5l filler (Activ, GatPoly, Metal1 ... Metal4); TopMetal1 and the RF structures are not filled.
- LVS netlist: `netlist/TEST6967.cdl`, an empty subcircuit, because the chip contains no devices.
- DRC (full deck incl. antenna, and minimum = precheck), Magic DRC and LVS were run on this file; evidence in
  `doc/Signoff.md`.
