"""memory cloud image: the remembered closet inside a thought-cloud shape. python3 02c_cloud.py"""
HERE = "/home/user/Muhammed/blender/ClosetBathroom_v002/"
from PIL import Image, ImageDraw, ImageFilter
im = Image.open(HERE + "assets/closet_memory.png").convert("RGBA").resize((512, 512))
mask = Image.new("L", (512, 512), 0); dm = ImageDraw.Draw(mask)
for cx, cy, r in ((256, 256, 190), (120, 200, 110), (392, 200, 110), (150, 360, 105), (362, 360, 105), (256, 110, 110), (256, 410, 100)):
    dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))
rim = mask.filter(ImageFilter.MaxFilter(15))
outim = Image.new("RGBA", (512, 512), (255, 255, 255, 0)); white = Image.new("RGBA", (512, 512), (250, 252, 255, 255))
outim.paste(white, (0, 0), rim); outim.paste(im, (0, 0), mask)
outim.save(HERE + "assets/memory_cloud.png")
