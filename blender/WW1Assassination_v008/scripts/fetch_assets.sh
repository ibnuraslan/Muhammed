#!/bin/bash
# WW1Assassination v008 assets. bash fetch_assets.sh <assets_dir>
# 1) MakeHuman community CC0 garment packs into MPFB's clothes library (suits, shirts, trousers, skirts, hats)
# 2) Sketchfab CC-BY models (needs a Sketchfab API session: the studio proxy injects it): touring car, Browning 1910 pistol
# 3) Poly Haven CC0 textures + sky HDRI, Natural Earth 1:50m countries (public domain) for the map
set -e
A=${1:?assets dir}; mkdir -p "$A"; T=$(mktemp -d)
D=${MPFB_DATA:-/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data}
for n in shirts01 pants01 suits01 hats01 skirts01; do
  curl -sf -o "$T/$n.zip" "https://files.makehumancommunity.org/asset_packs/$n/${n}_cc0.zip"
  unzip -oq "$T/$n.zip" -d "$T/$n"; cp -r "$T/$n"/clothes/* "$D/clothes/"
done
sk() { curl -s "https://api.sketchfab.com/v3/models/$1/download" | python3 -c "import json,sys; print(json.load(sys.stdin)['glb']['url'])"; }
curl -sf -o "$A/car.glb" "$(sk 8cb1c1243c394144837a15f4722a2867)"
curl -sf -o "$A/pistol.glb" "$(sk 9896a6cffc67468bad87da97e396995a)"
HERE=$(cd "$(dirname "$0")" && pwd)
python3 -I "$HERE/../../pipeline/fetch_polyhaven.py" "$A/ph" 1k cobblestone_floor_08 yellow_plaster_02 white_stucco red_plaster_weathered plaster_stone_wall_01 castle_brick_07 kloofendal_48d_partly_cloudy_puresky
curl -sf -o "$A/ne50.geojson" https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
echo "assets in $A"
