#!/bin/bash
# Re-render the shots lifted by edit/exposure_fix.json at the storyboard settings and print look vs plain again.
cd /home/user/Muhammed/projects/phone-banker
source ~/render_env/env.sh
export PYTHONPATH=scenes:../../nvidia_doc/scenes
python3 -c "import json; [print(k) for k in json.load(open('edit/exposure_fix.json'))]" | while IFS=/ read -r st mv; do
  name=$(awk -v s=$st -v m=$mv '$3==s && $4==m {print $2}' out/daycheck_list.txt); part=${name%%_*}
  secs=$(awk -v n=$name '$2==n {print $5}' out/daycheck_list.txt)
  d=out/storyboard_fix/$part/$name; mkdir -p $d
  [ -f $d/plate.png ] || python edit/pb_exec.py $secs run $st $mv --still --t 0.5 --pct 25 --samples 12 --out $d > $d.log 2>&1 || echo "FAIL $name"
  python3 -c "
from PIL import Image, ImageStat
def L(p):
    r,g,b=[c/255 for c in ImageStat.Stat(Image.open(p).convert('RGB')).mean]; return 0.2126*r+0.7152*g+0.0722*b
print('$name', 'fixed %.3f  plain %.3f' % (L('$d/plate.png'), L('out/storyboard_plain/$part/$name/plate.png')))" | tee -a review/daycheck_fix.txt
done
