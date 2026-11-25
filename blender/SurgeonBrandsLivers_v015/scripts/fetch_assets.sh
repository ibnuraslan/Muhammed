#!/bin/bash
# Real garments: MakeHuman community asset packs (CC0), unpacked into MPFB's clothes library before 01_build.py.
set -e
D=${1:-/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data}
T=$(mktemp -d)
for n in shirts01 pants01 suits01; do
  curl -sf -o "$T/$n.zip" "https://files.makehumancommunity.org/asset_packs/$n/${n}_cc0.zip"
  unzip -oq "$T/$n.zip" -d "$T/$n"
  cp -r "$T/$n"/clothes/* "$D/clothes/"
done
echo "garments installed into $D/clothes"
