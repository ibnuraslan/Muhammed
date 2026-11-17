import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
mp4, out = sys.argv[1:3]
cells = [(7549, "c5_16 f7549"), (7550, "c5_16 last f7550"), (7551, "PATCH first f7551"), (7552, "patch f7552"),
         (7590, "patch f7590 (lights row 1 off)"), (7640, "patch f7640"), (7700, "patch f7700 (was black)"), (7760, "patch f7760"),
         (7820, "patch f7820"), (7862, "patch f7862 (dark end)"), (7875, "PATCH last f7875"), (7876, "c5_18 first f7876")]
want = [f for f, _ in cells]; sel = "+".join(f"eq(n\\,{f-1})" for f in want)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"select='{sel}',scale=640:272", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 272, 640, 3); assert len(fr) == len(cells)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
cols = 4; sh = Image.new("RGB", (cols * 646 + 6, 3 * 300 + 40), (16, 16, 20)); d = ImageDraw.Draw(sh)
d.text((8, 10), "NVIDIA PART 2 v2 — c5_17 patch spliced in (master 7551-7875), seams + captions", fill=(240, 240, 240), font=F)
for i, (f, t) in enumerate(cells):
    x = 6 + (i % cols) * 646; y = 40 + (i // cols) * 300
    d.text((x, y), t, fill=(240, 200, 120), font=F); sh.paste(Image.fromarray(fr[i]), (x, y + 24))
sh.save(out, quality=88); print(out)
