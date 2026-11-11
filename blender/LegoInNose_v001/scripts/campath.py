"""Dump the camera path and draw it (top view + height).  blender -b anim.blend --python campath.py -- out.jpg"""
import sys, json, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; P = []
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); p = cam.matrix_world.translation; P.append((f, p.x, p.y, p.z, cam.data.lens))
json.dump(P, open(out.replace(".jpg", ".json"), "w"))
import subprocess
subprocess.run(["python3", "-I", "-c", r'''
import json,sys
from PIL import Image, ImageDraw
P=json.load(open(sys.argv[1])); W,H=1400,900; im=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(im)
def top(x,y): return (60+(x+3)*95, 520-(y+3)*70)
def side(f,z): return (60+f/2310*1280, 880-(z+8)*35)
for x0,y0,x1,y1,c in ((-2.8,-2.6,2.8,2.4,"#c96"),(2.8,-1.2,6.4,2.4,"#69c"),(6.4,-0.2,9,2.4,"#6a9")):
    d.rectangle([top(x0,y1),top(x1,y0)],outline=c,width=3)
d.text(top(-2.7,2.2),"living room",fill="#c96"); d.text(top(2.9,2.2),"bedroom",fill="#69c"); d.text(top(6.5,2.2),"bathroom",fill="#6a9")
d.text((60,10),"CAM_Film path, top view (studio is below the floor, z=-7; red = in the studio/tunnel)",fill="black")
for a,b in zip(P,P[1:]):
    c=(220,40,40) if a[3]<-0.3 else (30,30,30); d.line([top(a[1],a[2]),top(b[1],b[2])],fill=c,width=2)
    d.line([side(a[0],a[3]),side(b[0],b[3])],fill=c,width=2)
for p in P[::30]:
    d.text(top(p[1],p[2]),"%.0fs"%((p[0]-1)/60),fill=(0,0,200)); d.text(side(p[0],p[3]),"%.0f"%((p[0]-1)/60),fill=(0,0,200))
d.text((60,560),"camera height z over time (s); dips = the two dives into the cross-section studio",fill="black")
im.save(sys.argv[2],quality=90)
''', out.replace(".jpg", ".json"), out])
print("CAMPATH", out)
