#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Adds the seal ring and the PDK filler. The filler runs with patched fill distances (Metal1/2/4 0.75 um, Metal3 1.25 um,
# TopMetal1 3.05 um, as in scripts/add_logo_fill.sh of the template ihp-sg13cmos5l-ams-chip-template), so that
# Metal1..4 reach the global density of 35 % (Mn.j).
#
#   seal_fill.sh <name> <width_um> <height_um>
#
# Reads <name>_core.gds in the current directory, writes <name>_seal.gds and <name>_filled.gds.
set -eu
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"
NAME="$1"; W="$2"; H="$3"
HERE="$PWD"

# sealring.py passes "width" to the PCell parameter w (y axis) and "height" to l (x axis), hence the swap
in_container klayout -n "$TECH_NAME" -zz -r "$KL/tech/scripts/sealring.py" -rd width="$H" -rd height="$W" \
    -rd input="${NAME}_core.gds" -rd output="${NAME}_seal.gds" > "seal_$NAME.log" 2>&1
echo "### seal ring done"

FP="$HERE/fill_pdk_patched"
MD="$FP/$PDK_NAME/libs.tech/klayout/tech/macros"
rm -rf "$FP"; mkdir -p "$MD"
cp "$KL/tech/macros/sg13cmos5l_filler_ActGatP.lym" "$KL/tech/macros/sg13cmos5l_filler_Metal.lym" "$MD/"
sed -i -e "s/'distance_m1' => [0-9.]*/'distance_m1' => 0.75/" -e "s/'distance_m2' => [0-9.]*/'distance_m2' => 0.75/" \
       -e "s/'distance_m3' => [0-9.]*/'distance_m3' => 1.25/" -e "s/'distance_m4' => [0-9.]*/'distance_m4' => 0.75/" \
       -e "s/'distance_tm1' => [0-9.]*/'distance_tm1' => 3.05/" "$MD/sg13cmos5l_filler_Metal.lym"
grep -q "'distance_m3' => 1.25" "$MD/sg13cmos5l_filler_Metal.lym" || { echo "patching the fill distances failed"; exit 1; }
FILL_ROOT="$FP" in_container klayout -n "$TECH_NAME" -zz -r "$KL/tech/scripts/filler.py" \
    -rd output_file="${NAME}_filled.gds" "${NAME}_seal.gds" > "fill_$NAME.log" 2>&1
echo "### filler done"
