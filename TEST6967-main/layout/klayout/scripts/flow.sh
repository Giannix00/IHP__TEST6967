#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Complete flow of TEST6967: generator, seal ring, filler, release GDS, comparison with the released GDS, sign-off.
# Stops at the first failure.
#
#   PDK_TREE=/path/to/IHP-Open-PDK IIC_SIF=/path/to/iic-osic-tools.sif bash scripts/flow.sh [build_dir]
set -eu
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPTS/env.sh"
REPO="$(cd "$SCRIPTS/../../../.." && pwd)"
RELEASE="$REPO/release/v.1.0.0"
NAME=TEST6967
OUT="${1:-build}"
mkdir -p "$OUT"
cd "$OUT"

in_container python3 "$SCRIPTS/build_core.py" --name "$NAME" --x 1000 --y 1000 --network 65 70 65 60 --t_stub 160 \
    --gnd_pad 510 895 --gnd_sym --bond_pad 70 --cal 430 300 700 --probe_test 500 --land_pads 792 208 --plate_x 345
bash "$SCRIPTS/seal_fill.sh" "$NAME" 1000 1000
in_container python3 "$SCRIPTS/make_release.py" "${NAME}_filled.gds" "$NAME.gds" "$NAME"
in_container python3 "$SCRIPTS/compare_gds.py" "$NAME.gds" "$RELEASE/gds/$NAME.gds"
cp "$RELEASE/netlist/$NAME.cdl" .
bash "$SCRIPTS/signoff.sh" "$NAME"
echo "### flow finished"
