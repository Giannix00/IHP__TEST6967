# DRC and LVS evidence, TEST6967 v.1.0.0

All runs are on the release file `gds/TEST6967.gds` itself (sha256
`7d3c4f6d8a55f32d4782d62112d1f959134d386959e32dff0d1361fadfde6cfd`), top cell `TEST6967`, seal ring and filler
included, and on the release netlist `netlist/TEST6967.cdl` (sha256
`e4b2d50075f2ab6f208fe987872981c6f4a9ffa37495069f53d237dd0e822ec7`). Run date 2026-11-07 (UTC).

| Tool | Version |
| --- | --- |
| PDK (DRC and LVS decks) | IHP-Open-PDK dev `c6562037497437ce6bc689e633e5b45abf9bbccb` (2026-10-25), `ihp-sg13cmos5l` |
| KLayout | 0.30.9 (iic-osic-tools container 2026.07) |
| Magic | 8.3 revision 678 with the `ihp-sg13cmos5l` tech file of the same container, run through `sak-drc.sh` |

## DRC

| Run | Invocation | Switch, from the log | Result, from the log | Log | Database |
| --- | --- | --- | --- | --- | --- |
| Minimum, the foundry precheck rule set | `run_drc.py --path=TEST6967.gds --topcell=TEST6967 --minimum_drc --mp=8` | Minimum DRC enabled: true | No DRC violations | [drc_min.log](drc_min.log) | [drc_min.lyrdb](drc_min.lyrdb) |
| Full deck incl. antenna, density and maximal rule set | `run_drc.py --path=TEST6967.gds --topcell=TEST6967 --antenna --mp=8` | Minimum DRC enabled: false | No DRC violations | [drc_full.log](drc_full.log) | [drc_full.lyrdb](drc_full.lyrdb) |
| Full deck, flat | `run_drc.py --path=TEST6967.gds --topcell=TEST6967 --run_mode=flat --mp=8` | Minimum DRC enabled: false | No DRC violations | [drc_flat.log](drc_flat.log) | – |
| Magic | `sak-drc.sh -d -m -f "*" TEST6967.gds` | – | COUNT: 0, "No DRC errors in <TEST6967> found" | [magic_drc.log](magic_drc.log) | [magic_drc.rpt](magic_drc.rpt) |

`run_drc.py` is the script of the PDK (`ihp-sg13cmos5l/libs.tech/klayout/tech/drc/run_drc.py`).
`--minimum_drc` sets the deck switch `precheck_drc`, which the decks print as `Minimum DRC enabled`. The full
run leaves the switch false because it checks the whole deck, not the reduced set. Neither database has a
violation item (586 rule categories in the full run, 82 in the minimum run).

## LVS

Release GDS against [`netlist/TEST6967.cdl`](../netlist/TEST6967.cdl), PDK script
`ihp-sg13cmos5l/libs.tech/klayout/tech/lvs/run_lvs.py`, flat, `--purge --purge_nets --ignore_top_ports_mismatch`.
Result, from the log: Netlists match (Status | PASS, 0 warnings, 0 errors).
Log: [lvs.log](lvs.log), database: [lvs.lvsdb](lvs.lvsdb), extracted netlist: [lvs_extracted.cir](lvs_extracted.cir).

TEST6967 is purely passive: metal lines, pads and ground on Metal1 ... TopMetal1, no devices. What the
comparison establishes, and what not:

- Checked: the layout extracts no device. The schematic netlist is an empty subcircuit, and the comparison
  passes; a device in the layout (e.g. from a stray Activ/GatPoly overlap outside the filler) would fail it.
  The CMOS5L forbidden-layer check in the LVS run passes.
- Not checked: connectivity of the metal structures. Without devices every net is device-free and purged, so the
  extracted netlist is empty. The pin labels on TopMetal1 pin (126/25) are therefore not compared
  (`--ignore_top_ports_mismatch`).

## Rebuild

`TEST6967-main/layout/klayout/scripts/flow.sh` rebuilt the chip from the generator on 2026-11-07. `compare_gds.py` against
this release: `32 layers compared by XOR, 18 labels, 11 subcells: IDENTICAL`. DRC full, DRC minimum, LVS and Magic DRC of
the rebuild are clean. Its checksum differs, because KLayout writes the build time into the GDS.

## gdscheck

[gdscheck](https://github.com/aesc-silicon/gdscheck) is an independent DRC engine with its own rule decks. The container
release 2026.07 does not contain it, so it was built from source inside that container: tag `v0.2.0` (`dd72f5c0`) and
`main` at `07aed349`. Both report the version `gdscheck 0.2.0`.

    gdscheck run --input TEST6967.gds --process ihp-sg13cmos5l --suite <suite> --topcell TEST6967 --threads 8

Suites main, core, precheck, recommended, density and antenna: exit code 0, `Status: PASS`, no violation item, in both
builds. Logs: [gdscheck_v0.2.0.log](gdscheck_v0.2.0.log), [gdscheck_07aed349.log](gdscheck_07aed349.log).

## IHP online tape-in check

Online check at dk.ihp-microelectronics.com on 2026-11-07 (Calibre 2026.1.17.11). It reports five rules:

| Reported | Count | Meaning in the `ihp-sg13g2` deck | `ihp-sg13cmos5l` deck |
| --- | --- | --- | --- |
| TV1.c | 100 | Min. Metal5 enclosure of TopVia1 | Min. Metal4 enclosure of TopVia1, no violation |
| Pad.i | 29 | dfpad without TopMetal2 not allowed | dfpad without TopMetal1 not allowed, no violation |
| M5.j | 1 | Metal5 density | rule does not exist |
| M5Fil.h | 1 | Metal5 and Metal5:filler coverage ratio | rule does not exist |
| TM2.c | 1 | Min. global TopMetal2 density | rule does not exist |

The layout cannot meet these five as defined for SG13G2: Metal5 and TopMetal2 are forbidden layers in SG13CMOS5L
(`SG13CMOS5L_os_layout_rules.pdf`, Rev. 0.1, section 3.2), and in this process TopVia1 sits on Metal4 and TopMetal1 is the
top metal. No other rule is reported.
