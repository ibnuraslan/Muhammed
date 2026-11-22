W=$1; spp=$2; pre=$3; shift 3
for f in "$@"; do echo "== $f"; /opt/blender/blender-5.2.2-linux-x64/blender -b -P $W/$f.py -- $W/${pre}$f.png $spp 2>&1 | grep -iE 'error|Traceback|Saved' | head -3; done
