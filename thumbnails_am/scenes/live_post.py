"""Post for the live test: upscale 960x540 frames to 1080p (Lanczos + light unsharp), add the date-stamp and section
tag overlay, write frames for ffmpeg. Also builds the upscaled-vs-native side-by-side with a 100% figure crop.
    python3 live_post.py <frames_dir> <out_dir> <font.ttf> [native_frame60.png]"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, dst, F = sys.argv[1], sys.argv[2], sys.argv[3]
native = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(dst, exist_ok=True)


def overlay(up):
    d = ImageDraw.Draw(up); fs = ImageFont.truetype(F, 26); fb = ImageFont.truetype(F, 64); cx = 960
    t1 = '16 FEB'; w1 = d.textlength(t1, font=fs); d.text((cx - w1 / 2, 40), t1, font=fs, fill=(235, 232, 220))
    t2 = '2003'; w2 = d.textlength(t2, font=fb); d.text((cx - w2 / 2, 66), t2, font=fb, fill=(245, 242, 232))
    yl = 66 + 48
    d.line([(cx - w2 / 2 - 150, yl), (cx - w2 / 2 - 22, yl)], fill=(235, 232, 220), width=2)
    d.line([(cx + w2 / 2 + 22, yl), (cx + w2 / 2 + 150, yl)], fill=(235, 232, 220), width=2)
    ft = ImageFont.truetype(F, 34); tag = 'THE VAULT'; tw = d.textlength(tag, font=ft); x0, y0 = 48, 44
    d.rectangle([x0, y0, x0 + tw + 36, y0 + 58], outline=(235, 232, 220), width=3); d.text((x0 + 18, y0 + 5), tag, font=ft, fill=(245, 242, 232))
    return up


def upscale(im):
    return im.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))


for p in sorted(glob.glob(os.path.join(src, "f_*.png"))):
    overlay(upscale(Image.open(p).convert('RGB'))).save(os.path.join(dst, os.path.basename(p)), compress_level=1)
if native:
    up = upscale(Image.open(os.path.join(src, "f_0060.png")).convert('RGB')); nat = Image.open(native).convert('RGB')
    W, H = 960, 540; pad = 16; lab = 40
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    # 100% crop around the lead figure: find the brightest pale area in the lower half
    import numpy as np
    a = np.asarray(nat.convert('L'), float); a[:400] = 0
    yx = np.unravel_index(np.argmax(np.convolve(a.sum(1), np.ones(40), 'same')), a.shape[:1])[0]
    cxp = int(np.argmax(np.convolve(a[max(0, yx - 150):yx + 150].sum(0), np.ones(60), 'same')))
    box = (max(0, cxp - 240), max(0, yx - 220), max(0, cxp - 240) + 480, max(0, yx - 220) + 440)
    sh = Image.new('RGB', (2 * W + 3 * pad, H + 440 + 2 * lab + 3 * pad), (18, 18, 20)); d = ImageDraw.Draw(sh)
    d.text((pad, pad), 'Frame 60: 960x540 render, upscaled to 1080p', fill=(240, 220, 170), font=f)
    d.text((2 * pad + W, pad), 'Frame 60: native 1920x1080 render', fill=(240, 220, 170), font=f)
    sh.paste(up.resize((W, H), Image.LANCZOS), (pad, pad + lab)); sh.paste(nat.resize((W, H), Image.LANCZOS), (2 * pad + W, pad + lab))
    y2 = 2 * pad + lab + H
    d.text((pad, y2), '100% crop (1080p), upscaled', fill=(240, 220, 170), font=f)
    d.text((2 * pad + W, y2), '100% crop (1080p), native', fill=(240, 220, 170), font=f)
    sh.paste(up.crop(box), (pad + 240, y2 + lab)); sh.paste(nat.crop(box), (2 * pad + W + 240, y2 + lab))
    sh.save(os.path.join(os.path.dirname(dst.rstrip('/')), 'upscaled_vs_native.jpg'), quality=90)
print("POST DONE")
