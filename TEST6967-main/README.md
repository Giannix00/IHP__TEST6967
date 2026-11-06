# TEST6967-main

Source of the top cell `TEST6967`.

- `layout/klayout/scripts/`: layout generator and build flow, see below. The released layout (seal ring and filler
  included) is [`release/v.1.0.0/gds/TEST6967.gds`](../release/v.1.0.0/gds/TEST6967.gds).
- There is no schematic: the chip contains no devices, only metal lines, pads and ground on Metal1 ... TopMetal1.
  The LVS netlist is [`release/v.1.0.0/netlist/TEST6967.cdl`](../release/v.1.0.0/netlist/TEST6967.cdl).

## Rebuilding

Requires apptainer, the iic-osic-tools image, release 2026.07 (KLayout 0.30.9, Magic 8.3 revision 678), and an
IHP-Open-PDK checkout at the commit given in [`doc/info.json`](../doc/info.json):

    git clone https://github.com/IHP-GmbH/IHP-Open-PDK
    git -C IHP-Open-PDK checkout c6562037497437ce6bc689e633e5b45abf9bbccb
    cd TEST6967-main/layout/klayout
    PDK_TREE=/path/to/IHP-Open-PDK IIC_SIF=/path/to/iic-osic-tools.sif bash scripts/flow.sh

`flow.sh` writes to `build/`, runs these steps in order and stops at the first failure:

1. `build_core.py`: draws the core layout, `TEST6967_core.gds`. All dimensions come from the constants at the top of
   the script and from the command line in `flow.sh`.
2. `seal_fill.sh`: seal ring PCell and PDK filler with patched fill distances, `TEST6967_filled.gds`.
3. `make_release.py`: top cell name, seal ring area label and save options of Open-Silicon-MPW, `TEST6967.gds`. It
   checks by XOR that the geometry is unchanged.
4. `compare_gds.py`: compares the rebuilt `TEST6967.gds` with the released GDS (XOR of every layer, all labels,
   subcells, bounding box).
5. `signoff.sh`: PDK DRC, full deck with antenna and minimum deck, PDK LVS, and Magic DRC through `drc_magic.sh`.

KLayout writes the build time into the GDS, so a rebuild has the same geometry but a new checksum.
