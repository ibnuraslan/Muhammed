#!/bin/bash
# Low-res motion preview of one move: preview_mp4.sh set move seconds fps outdir   (env PCT=44 SAMPLES=8)
# Renders N = seconds*fps frames with run.py --anim, then ffmpeg -> 24 fps MP4 (motion-interpolated when fps < 24).
set -e
SET=$1; MV=$2; SEC=$3; FPS=$4; OUT=$(realpath -m "$5"); cd /home/user/Muhammed; source ~/render_env/env.sh
N=$(python3 -c "print(int(round($SEC*$FPS)))"); D=$OUT/frames/${SET}_${MV}; mkdir -p $D
PYTHONPATH=projects/killer-in-house/scenes:nvidia_doc/scenes python nvidia_doc/scenes/run.py $SET $MV --anim $N --pct ${PCT:-44} --samples ${SAMPLES:-8} --out $D > $D.log 2>&1
VF="minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1"; [ "$FPS" -ge 24 ] && VF="fps=24"
ffmpeg -v error -y -framerate $FPS -pattern_type glob -i "$D/f*.png" -vf "$VF,scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart $OUT/${SET}_${MV}.mp4
echo "[mp4] $OUT/${SET}_${MV}.mp4"
