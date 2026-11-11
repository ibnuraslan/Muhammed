import sys,glob
from PIL import Image, ImageDraw
fs=sorted(glob.glob(sys.argv[1]+"/f*.jpg")); ims=[Image.open(f) for f in fs]
w,h=ims[0].size; S=Image.new("RGB",(w*len(ims),h))
for i,(f,im) in enumerate(zip(fs,ims)):
    ImageDraw.Draw(im).text((3,3),f.split("/")[-1],fill=(255,255,0)); S.paste(im,(i*w,0))
S.save(sys.argv[2],quality=85)
