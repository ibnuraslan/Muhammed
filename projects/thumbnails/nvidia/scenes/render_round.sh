#!/bin/bash
# Render every concept and build the labelled sheet.  bash scenes/render_round.sh <outdir> <pct> <samples>
cd "$(dirname "$0")/.."
source ~/render_env/env.sh
export PYTHONPATH=scenes:../../../nvidia_doc/scenes
O=${1:-out/r1}; P=${2:-50}; S=${3:-96}; mkdir -p $O
for n in watched flash chip cctv; do
  [ -f $O/$n.png ] || python scenes/thumb.py $n --pct $P --samples $S --out $O > $O/$n.log 2>&1; echo "rendered $n $?"
done
for v in capitol aisle; do
  [ -f $O/split_$v.png ] || python scenes/thumb.py split --variant $v --pct $P --samples $S --out $O > $O/split_$v.log 2>&1; echo "rendered split_$v $?"
done
python -c "from th_split import compose_split; compose_split('$O/split_capitol.png', '$O/split_aisle.png', '$O/split.png')"
python scenes/contact.py $O/contact_sheet.jpg "1 Watched=$O/watched.png" "2 Flash=$O/flash.png" "3 The handoff=$O/chip.png" "4 CCTV=$O/cctv.png" "5 Two worlds=$O/split.png"
echo "ALL DONE"
