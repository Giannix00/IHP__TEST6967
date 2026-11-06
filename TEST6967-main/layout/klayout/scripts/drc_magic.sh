#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Magic DRC through sak-drc.sh (flags as "make magic-drc" of the template ihp-sg13cmos5l-ams-chip-template).
#
#   drc_magic.sh <name>
#
# Reads <name>.gds in the current directory, writes magic_<name>/.
set -u
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"
NAME="$1"
HERE="$PWD"
OUT="$HERE/magic_$NAME"
rm -rf "$OUT"; mkdir -p "$OUT"
cat > "$OUT/inner.sh" <<'INNER'
set -u
NAME="$1"; HERE="$2"; PDK_TREE="$3"; PDK_NAME="$4"; OUT="$5"
# apptainer exec starts without the login environment of the container: set the tool paths here
for d in /foss/tools/bin /foss/tools/sak /foss/tools/magic/bin /foss/tools/klayout; do [ -d "$d" ] && PATH="$d:$PATH"; done
for t in magic sak-drc.sh; do
    command -v $t > /dev/null || { p=$(find /foss/tools -maxdepth 4 -name "$t" -type f 2>/dev/null | head -1)
                                   [ -n "$p" ] && PATH="$(dirname "$p"):$PATH"; }
done
export PATH
echo "### container ${IIC_OSIC_TOOLS_VERSION:-?}"
for t in magic sak-drc.sh; do echo "### $t: $(command -v $t || echo missing)"; done
# the magic tech file comes from the PDK checkout if it has one, else from the container
MAGIC_ROOT=""
for r in "$PDK_TREE" /foss/pdks; do
    [ -f "$r/$PDK_NAME/libs.tech/magic/$PDK_NAME.magicrc" ] && { MAGIC_ROOT="$r"; break; }
done
echo "### magic tech root: ${MAGIC_ROOT:-none}"
[ -n "$MAGIC_ROOT" ] || exit 1
export PDK_ROOT="$MAGIC_ROOT" PDK="$PDK_NAME" PDKPATH="$MAGIC_ROOT/$PDK_NAME" STD_CELL_LIBRARY=sg13cmos5l_stdcell
export SPICE_USERINIT_DIR="$PDKPATH/libs.tech/ngspice" KLAYOUT_PATH="$PDKPATH/libs.tech/klayout"
sak-drc.sh -d -m -f "*" -w "$OUT" "$HERE/$NAME.gds" > "$OUT/sak_magic.log" 2>&1
echo "### sak-drc.sh rc=$?"
INNER
apptainer exec --env PDK="$PDK_NAME" "$IIC_SIF" bash "$OUT/inner.sh" "$NAME" "$HERE" "$PDK_TREE" "$PDK_NAME" "$OUT" \
    > "$OUT/run.log" 2>&1
