# SPDX-License-Identifier: Apache-2.0
# Settings shared by the flow scripts. All tools run in the iic-osic-tools container.
#   PDK_TREE  IHP-Open-PDK checkout at the commit given in doc/info.json
#   IIC_SIF   iic-osic-tools apptainer image, release 2026.07 (KLayout 0.30.9, Magic 8.3 revision 678)
: "${PDK_TREE:?set PDK_TREE to an IHP-Open-PDK checkout}"
: "${IIC_SIF:?set IIC_SIF to the iic-osic-tools apptainer image}"
PDK_NAME=ihp-sg13cmos5l
TECH_NAME=sg13cmos5l
KL="$PDK_TREE/$PDK_NAME/libs.tech/klayout"
[ -d "$KL/tech" ] || { echo "$PDK_NAME not found in $PDK_TREE"; exit 1; }
KL_ENV=(--env PATH=/foss/tools/klayout:/usr/local/bin:/usr/bin:/bin --env LD_LIBRARY_PATH=/foss/tools/klayout
        --env PDK="$PDK_NAME" --env KLAYOUT_PATH="$KL")

# Run a command in the container. PDK_ROOT is PDK_TREE unless the caller sets FILL_ROOT.
in_container() {
    apptainer exec "${KL_ENV[@]}" --env PDK_ROOT="${FILL_ROOT:-$PDK_TREE}" "$IIC_SIF" "$@"
}
