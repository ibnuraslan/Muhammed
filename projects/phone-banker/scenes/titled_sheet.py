"""Preview sheet with chapter titles composited over the title shots (labels containing 'CHAPTER' get the card)."""
import sys, os
sys.path.insert(0, "/home/user/Muhammed/nvidia_doc/scenes")
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
rows = (len(pairs) + 1) // 2
S = Image.new("RGB", (W * 2, rows * (H + BAR)), (14, 16, 20)); d = ImageDraw.Draw(S)
for i, (label, path) in enumerate(pairs):
    x, y = (i % 2) * W, (i // 2) * (H + BAR)
    if "," in path:                                   # a strip of frames from one shot, side by side
        ps = path.split(","); im = Image.new("RGB", (W, H), (0, 0, 0)); w3 = W // len(ps)
        for j, pp in enumerate(ps):
            if os.path.exists(pp):
                src = Image.open(pp).convert("RGB"); sw, sh = src.size
                crop = src.crop((sw // 2 - int(sh * w3 / H) // 2, 0, sw // 2 + int(sh * w3 / H) // 2, sh)).resize((w3, H))
                im.paste(crop, (j * w3, 0))
    else:
        im = Image.open(path).convert("RGB").resize((W, H)) if os.path.exists(path) else Image.new("RGB", (W, H), (60, 0, 0))
    if "CHAPTER" in label:
        import title_card
        small, big = label.split("+")[1].strip().split(" / ")
        tp = f"/tmp/claude-0/-home-user-Muhammed/f9e50632-c631-5881-82fb-617944a2f28d/scratchpad/title_{i}.png"
        title_card.title_image(small, big, tp)
        t = Image.open(tp).convert("RGBA").resize((W, H)); im = im.convert("RGBA"); im.alpha_composite(t); im = im.convert("RGB")
    S.paste(im, (x, y + BAR)); d.text((x + 14, y + 9), label, font=font, fill=(235, 236, 240))
os.makedirs(os.path.dirname(out), exist_ok=True)
S.save(out, quality=86)
