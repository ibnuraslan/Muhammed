#!/bin/bash
# low-res moving preview of one film: tools/preview.sh f1  -> out/preview/seldom_intro_f1_preview.mp4
D=$(cd "$(dirname "$0")/.." && pwd); B=/opt/blender/blender-5.2.2-linux-x64/blender; F=$1
mkdir -p "$D/out/preview" "$D/out/logs"
for s in A B C D; do
  rm -rf "$D/out/frames/$F$s"
  PCT=${PCT:-33} SPP=${SPP:-12} CLIP_STRICT=0 "$B" -b --factory-startup -P "$D/run_anim.py" -- $F $s > "$D/out/logs/prev_$F$s.log" 2>&1
  echo "$F$s $(grep -E 'CLIPRESULT|RENDERED_ANIM|Traceback|Error:' "$D/out/logs/prev_$F$s.log" | grep -v CUEW | tr '\n' ' ')"
done
: > "$D/out/preview/$F.txt"
for s in A B C D; do for f in "$D/out/frames/$F$s"/f*.jpg; do echo "file '$f'" >> "$D/out/preview/$F.txt"; echo "duration 0.0416667" >> "$D/out/preview/$F.txt"; done; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$D/out/preview/$F.txt" -vf "fps=24,scale=854:-2" -c:v libx264 -pix_fmt yuv420p -crf 23 "$D/out/preview/seldom_intro_${F}_preview.mp4"
ls -la "$D/out/preview/seldom_intro_${F}_preview.mp4"
