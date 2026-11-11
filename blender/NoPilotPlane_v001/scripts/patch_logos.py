"""Remove the printed emblem from MakeHuman shirt textures (no logos on clothes). python3 -I patch_logos.py <src_clothes_dir> <out_dir>
Each emblem disc is replaced by plain fabric copied from a clean spot on the same shirt front, feathered at the edge."""
import sys, numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
# name: (emblem cx, cy, r, source cx, cy)  in UV fractions
SPOT = {"female_casualsuit01": (0.775, 0.215, 0.105, 0.63, 0.30), "male_casualsuit02": (0.56, 0.17, 0.07, 0.56, 0.31),
        "male_casualsuit04": (0.545, 0.165, 0.095, 0.545, 0.27)}
for name, (cx, cy, r, sx, sy) in SPOT.items():
    im = np.array(Image.open("%s/%s/%s_diffuse.png" % (src, name, name)).convert("RGBA")).astype(np.float32); h, w = im.shape[:2]
    rx, ry = int(r * w), int(r * h)
    X, Y, SX, SY = int(cx * w), int(cy * h), int(sx * w), int(sy * h)
    dst = im[Y - ry:Y + ry, X - rx:X + rx]; T = w // 40; tile = im[SY - T:SY + T, SX - T:SX + T]
    sp = np.tile(np.concatenate([tile, tile[:, ::-1]], 1), (ry // T + 2, rx // (2 * T) + 2, 1))[:2 * ry, :2 * rx]
    yy, xx = np.mgrid[-ry:ry, -rx:rx]
    d = np.hypot(xx / rx, yy / ry); a = np.clip((1.0 - d) / 0.2, 0, 1)[..., None]
    im[Y - ry:Y + ry, X - rx:X + rx] = dst * (1 - a) + sp * a
    Image.fromarray(im.astype(np.uint8)).save("%s/%s_diffuse_nologo.png" % (out, name))
