#!/bin/bash
# Real garments + hair: MakeHuman community asset packs (CC0), unpacked into MPFB's library before 01_build.py.
set -e
D=${1:-/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data}
T=$(mktemp -d)
for n in suits01 shoes01 hair01; do
  curl -sf -o "$T/$n.zip" "https://files.makehumancommunity.org/asset_packs/$n/${n}_cc0.zip"; unzip -oq "$T/$n.zip" -d "$T/$n"
done
cp -r "$T"/suits01/clothes/toigo_male_suit_3 "$T"/shoes01/clothes/toigo_ankle_boots_male "$D/clothes/"
cp -r "$T"/hair01/hair/cortu_short_messy_hair "$D/hair/"
echo "assets installed into $D"
