import json, sys
from PIL import Image, ImageDraw
d=json.load(open(sys.argv[1])); W,H=1500,760; S=62; ox,oy=12.6,4.5
im=Image.new("RGB",(W,H),"white"); g=ImageDraw.Draw(im)
def P(x,y): return (int((x+ox)*S), int(H-(y+oy)*S))
rooms=[("Hearing",-12,-3.8,-3.5,3.5),("OR",-3.5,3.5,-3.5,3.5),("Home",3.8,9.8,-3,3),("Corridor",-0.2,3.4,3.6,7.2)]
for n,x0,x1,y0,y1 in rooms:
    g.rectangle([P(x0,y1),P(x1,y0)],outline=(120,120,120),width=2); g.text(P(x0+0.1,y1-0.3),n,fill=(80,80,80))
cols=[(220,40,40),(240,140,0),(180,180,0),(40,160,40),(0,150,200),(40,60,220),(140,40,200),(200,40,140)]
B=[1,301,565,637,781,1045,1231,1501,1711]
for i in range(len(d)-1):
    f=d[i][0]; b=max(k for k in range(8) if B[k]<=f)
    g.line([P(*d[i][1][:2]),P(*d[i+1][1][:2])],fill=cols[b],width=3)
    if f%60==1: g.ellipse([P(*d[i][1][:2])[0]-3,P(*d[i][1][:2])[1]-3,P(*d[i][1][:2])[0]+3,P(*d[i][1][:2])[1]+3],fill=(0,0,0)); g.text((P(*d[i][1][:2])[0]+4,P(*d[i][1][:2])[1]),"%ds"%(f//60),fill=(0,0,0))
for k in range(8): g.text((20,20+k*16),"beat %d"%(k+1),fill=cols[k])
g.text((20,160),"top view, camera position (dots = every 1 s). Studio dome is under the OR at z=-6 (dives at 2.2s and 17.6s).",fill=(0,0,0))
im.save(sys.argv[2],quality=90)
