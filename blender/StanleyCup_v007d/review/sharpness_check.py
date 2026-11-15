import sys, glob, numpy as np
from PIL import Image
d = sys.argv[1]; thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0
fs = sorted(glob.glob(d + "/f*.jpg")); out = []
for f in fs:
    a = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
    lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    # sharpness = 90th percentile of |laplacian| (robust to flat walls), and the fraction of the frame with any detail
    al = np.abs(lap); out.append((int(f[-8:-4]), float(np.percentile(al, 99)), float((al > 6).mean())))
for fr, p99, det in out:
    flag = " <<" if (thr and (p99 < thr)) else ""
    print("SH %4d p99=%5.1f detail=%.3f%s" % (fr, p99, det, flag))
