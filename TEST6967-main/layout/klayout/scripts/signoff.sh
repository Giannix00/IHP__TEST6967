#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Sign-off with the scripts of the PDK: run_drc.py full deck with --antenna, run_drc.py --minimum_drc (the foundry
# precheck rule set), run_lvs.py, and Magic DRC. Exit code 0 only if all four are clean.
#
#   signoff.sh <name>
#
# Reads <name>.gds and <name>.cdl in the current directory, writes drc_full/, drc_min/, lvs/, magic_<name>/ and *.log.
set -u
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPTS/env.sh"
NAME="$1"
HERE="$PWD"
{ echo "PDK $(git -C "$PDK_TREE" rev-parse HEAD) $(git -C "$PDK_TREE" log -1 --format=%cd)"
  echo "KLayout $(in_container klayout -v 2>&1)"
  sha256sum "$NAME.gds" "$NAME.cdl"; date -u; } > versions.txt

in_container python3 "$KL/tech/drc/run_drc.py" --path="$HERE/$NAME.gds" --topcell="$NAME" \
    --run_dir="$HERE/drc_full" --antenna --mp=8 > drc_full.log 2>&1
in_container python3 "$KL/tech/drc/run_drc.py" --path="$HERE/$NAME.gds" --topcell="$NAME" \
    --run_dir="$HERE/drc_min" --minimum_drc --mp=8 > drc_min.log 2>&1
in_container python3 "$KL/tech/lvs/run_lvs.py" --layout="$HERE/$NAME.gds" --netlist="$HERE/$NAME.cdl" \
    --topcell="$NAME" --run_dir="$HERE/lvs" --purge --purge_nets --ignore_top_ports_mismatch > lvs.log 2>&1
bash "$SCRIPTS/drc_magic.sh" "$NAME"

FAILED=0
check() {
    if grep -q "$2" "$3"; then echo "### $1: clean"; else echo "### $1: FAILED, see $3"; FAILED=1; fi
}
check "DRC full"    "No DRC violations"  drc_full.log
check "DRC minimum" "No DRC violations"  drc_min.log
check "LVS"         "Netlists match"     lvs.log
check "Magic DRC"   "No DRC errors in"   "magic_$NAME/sak_magic.log"
exit $FAILED
