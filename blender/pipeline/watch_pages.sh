#!/bin/bash
# watch_pages.sh PREVIEW_DIR [step=5] [audio.mp3]
# From preview.py frames: an MP4 at real speed (60/step fps, with the VO if given)
# and contact pages of EVERY preview frame (50 per page, 10x5). Read every page.
set -e
P=${1%/}; STEP=${2:-5}; AUD=$3
FPS=$((60 / STEP))
L=($(ls "$P"/f_*.jpg)); n=${#L[@]}
if [ -n "$AUD" ]; then
  ffmpeg -v error -y -framerate $FPS -pattern_type glob -i "$P/f_*.jpg" -i "$AUD" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$P/preview.mp4"
else
  ffmpeg -v error -y -framerate $FPS -pattern_type glob -i "$P/f_*.jpg" -c:v libx264 -pix_fmt yuv420p "$P/preview.mp4"
fi
mkdir -p "$P/pages"; rm -f "$P"/pages/*.jpg; i=0
for ((s=0; s<n; s+=50)); do
  i=$((i+1)); montage "${L[@]:s:50}" -tile 10x5 -geometry 200x356+1+1 "$P/pages/p$(printf %02d $i).jpg"
done
echo "$n frames -> $P/preview.mp4 and $i pages in $P/pages/"
