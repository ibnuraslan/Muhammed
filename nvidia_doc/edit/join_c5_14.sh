#!/bin/bash
# Join c5_14 (data hall, 252 f): frames 1-126 rendered here (W0) + c5_14_redo_part2.mp4 from W5 (frames 127-252).
#   bash edit/join_c5_14.sh <path/to/c5_14_redo_part2.mp4>   -> out/ch45_redo_render/c5_14_redo.mp4
# Part 1 is encoded exactly like render_redo.py (H.264 CRF 16, yuv420p, 24 fps, no audio); the halves are joined by
# stream copy (no re-encode), then the frame count is checked.
set -e
cd "$(dirname "$0")/.."
P2="$1"; R=out/ch45_redo_render
for f in $(seq 1 126); do [ -f $R/c5_14/f_$(printf %05d $f).png ] || { echo "missing frame $f"; exit 1; }; done
ffmpeg -y -v error -framerate 24 -start_number 1 -i $R/c5_14/f_%05d.png -frames:v 126 -c:v libx264 -crf 16 \
       -pix_fmt yuv420p -r 24 -an $R/c5_14_redo_part1.mp4
n2=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$P2")
[ "$n2" = 126 ] || { echo "part 2 has $n2 frames, expected 126"; exit 1; }
printf "file '%s'\nfile '%s'\n" "$PWD/$R/c5_14_redo_part1.mp4" "$(realpath "$P2")" > $R/c5_14_concat.txt
ffmpeg -y -v error -f concat -safe 0 -i $R/c5_14_concat.txt -c copy -movflags +faststart $R/c5_14_redo.mp4
n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $R/c5_14_redo.mp4)
echo "c5_14_redo.mp4: $n frames (expected 252)"; [ "$n" = 252 ]
