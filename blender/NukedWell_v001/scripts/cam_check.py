"""Camera-path clearance check. Run from blender/: python3 NukedWell_v001/scripts/cam_check.py [a-b ...]
Rebuilds the CAMK Catmull-Rom path. It reports frames where the lens is within 6 m of a solid prop or the crew, or crosses the ground skin slowly while looking down."""
import re,ast,numpy as np
import re,ast,numpy as np
s=open('NukedWell_v001/scripts/03_animate.py').read()
blk=s[s.index('CAMK = ['):]; blk=blk[blk.index('['):blk.index('\n]')+2]
K=ast.literal_eval(re.sub(r'#.*','',blk))
def catmull(keys):
    xs=[k[0] for k in keys]; ys=[np.array(k[1],float) for k in keys]
    def f(x):
        if x<=xs[0]: return ys[0]
        if x>=xs[-1]: return ys[-1]
        i=max(j for j in range(len(xs)-1) if xs[j]<=x); x0,x1=xs[i],xs[i+1]
        p0=ys[i-1] if i>0 else ys[i]-(ys[i+1]-ys[i]); p3=ys[i+2] if i+2<len(ys) else ys[i+1]+(ys[i+1]-ys[i])
        t0=xs[i-1] if i>0 else x0-(x1-x0); t3=xs[i+2] if i+2<len(xs) else x1+(x1-x0)
        p1,p2=ys[i],ys[i+1]; m1=(p2-p0)*((x1-x0)/(x1-t0)); m2=(p3-p1)*((x1-x0)/(t3-x0)); t=(x-x0)/(x1-x0)
        return p1*(2*t**3-3*t**2+1)+m1*(t**3-2*t**2+t)+p2*(-2*t**3+3*t**2)+m2*(t**3-t**2)
    return f
cp=catmull([(k[0],k[1]) for k in K]); ct=catmull([(k[0],k[2]) for k in K])
BOX={"cap":((-3,-4.6,0),(3,1.4,5)),"cab":((-9,22,0),(-4,27,4.5)),"mast":((-9,20,0),(-5,24,34)),"mixer":((-28,0,0),(-22,5,4)),
     "crewbunker":((-31,60,0),(-18,65,2)),"hoseA":((14,17,0),(19,24,2)),"hoseB":((-20,16,0),(-15,23,2)),"eng":((33,1,0),(38,7,2)),"collar":((-16,-4.7,0),(-12,-0.7,3)),"FT1":((18,36,0),(26,44,3.5)),"FT2":((-30,40,0),(-22,48,3.5)),"comp":((16.5,12.5,0),(19.5,15.5,1.5)),"cargo":((-44,26,0),(-36,34,3.5)),"engs":((38,-10,0),(43,-4,2)),"engs2":((33,1,0),(38,7,2)),"solAB":((14,17,0),(19,23,2)),"solCD":((-20,16,0),(-15,23,2)),"fire":((-6,-7.6,0),(6,4.4,60)),"crane_mast":((-9,20,0),(-5,24,34)),"derrick":((34,28,0),(46,40,38)),"wall":((-34,59,0),(-14,60.5,1.2))}
def dbox(p,b):
    lo,hi=np.array(b[0]),np.array(b[1]); return np.linalg.norm(np.maximum(0,np.maximum(lo-p,p-hi)))
import sys
rng=[tuple(map(int,a.split('-'))) for a in sys.argv[1:]] or [(1,2160)]
for a,b in rng:
  for f in range(a,b+1,5 if b-a>100 else 1):
    p=cp(f);t=ct(f);d=t-p;d/=np.linalg.norm(d)
    near=[f"{n}:{dbox(p,bx):.1f}" for n,bx in BOX.items() if dbox(p,bx)<6]
    flag=""
    if -0.3<p[2]<1.5 and d[2]<-0.25: flag+=" LOOKDOWN_SAND"
    if abs(p[2])<0.3: flag+=" SKIN"
    if near or flag: print(f, np.round(p,1), np.round(t,1), " ".join(near), flag)
