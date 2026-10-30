# DRC and LVS evidence, TEST6967 v.1.0.0

All runs are on the release file `gds/TEST6967.gds` itself (sha256
`cbc7a269f37bd8b1d452631a3b28ae79d30cc913196748920b5190ddf691b77c`), top cell `TEST6967`, seal ring and filler
included. Run date 2026-10-30 (UTC).

| Tool | Version |
| --- | --- |
| PDK (DRC and LVS decks) | IHP-Open-PDK dev `c6562037497437ce6bc689e633e5b45abf9bbccb` (2026-10-25), `ihp-sg13cmos5l` |
| KLayout | 0.30.9 (iic-osic-tools container 2026.07) |
| Magic | 8.3.589 with the `ihp-sg13cmos5l` tech file of the same container, run through `sak-drc.sh` |

## DRC

| Run | Invocation | Switch, from the log | Result, from the log | Log | Database |
| --- | --- | --- | --- | --- | --- |
| Minimum, the foundry precheck rule set | `run_drc.py --path=TEST6967.gds --topcell=TEST6967 --minimum_drc --mp=8` | Minimum DRC enabled: true | No DRC violations | [drc_min.log](drc_min.log) | [drc_min.lyrdb](drc_min.lyrdb) |
| Full deck incl. antenna, density and maximal rule set | `run_drc.py --path=TEST6967.gds --topcell=TEST6967 --antenna --mp=8` | Minimum DRC enabled: false | No DRC violations | [drc_full.log](drc_full.log) | [drc_full.lyrdb](drc_full.lyrdb) |
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
