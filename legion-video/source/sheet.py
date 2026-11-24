import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; frames = sys.argv[3].split(',') if len(sys.argv) > 3 else None
fs = sorted(glob.glob(d + '/*.jpg')) if not frames else [f'{d}/{int(x):05d}.jpg' for x in frames]
fs = [f for f in fs if os.path.exists(f)]
cols = 4; w, h = 480, 270; rows = (len(fs) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * h))
for i, f in enumerate(fs):
    im = Image.open(f).resize((w, h)); dr = ImageDraw.Draw(im); n = int(os.path.basename(f)[:5]); dr.text((6, 4), f'{n} {n/24:.2f}s', fill=(255, 255, 0)); S.paste(im, ((i % cols) * w, (i // cols) * h))
S.save(out, quality=85); print(out, len(fs))
