# TEST6967 v.1.0.0

First release. `gds/TEST6967.gds` is the GDS for submission (seal ring and filler included, checksum in
`gds/SHA256SUMS`), top cell `TEST6967`, saved with the KLayout options required by Open-Silicon-MPW (no PCell
context, zero-length paths eliminated, max. 8000 vertices, library name LIB, database unit 0.001 um).

- Seal ring: ihp-sg13cmos5l PCell at IHP-Open-PDK dev `c6562037`, 1000 x 1000 um. Its area label is
  `1.0 sq mm` (the PCell writes `1.0e-06 sq mm`).
- Fill: ihp-sg13cmos5l filler (Activ, GatPoly, Metal1 ... Metal4); TopMetal1 and the RF structures are not filled.
- LVS netlist: `netlist/TEST6967.cdl`, an empty subcircuit, because the chip contains no devices.
- DRC (full deck incl. antenna, flat run, and minimum = precheck), Magic DRC, LVS and gdscheck were run on this file;
  evidence in `doc/Signoff.md`, which also lists the result of the IHP online tape-in check.
- Layout generator and flow: `TEST6967-main/layout/klayout/scripts/`. A rebuild has the same geometry, but a new checksum,
  because KLayout writes the build time into the GDS.
- Metal1 ground: the grid stays clear of the seal ring corners and is separated from the solid corridor below the lines
  by a 2-um gap, so that the corridor is the only Metal1 plate wider than 35 um (slit density Slt.i, per polygon in
  gdscheck). Corridor and grid stay connected through the via stacks and the TopMetal1 plate.
- Metal2 pad shield below the probe-side signal pads (RF_PROBE, CAL_OPEN, CAL_SHORT, PROBE_TEST): the signal pad plus
  8 um, tied to the two ground pads by three 20-um strips per side, no Metal1 grid below it. RF_PROBE, CAL_OPEN and
  CAL_SHORT therefore carry the same pad, which OPEN/SHORT de-embedding removes.
