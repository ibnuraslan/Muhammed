import sys,glob,numpy as np,json
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
def feat(f):
    a=np.asarray(Image.open(f).convert('RGB').resize((427,240))).astype(np.int16)
    mx=a.max(2);mn=a.min(2)
    m=(mn>150)&(mx-mn<45)                       # neutral bright (white text/lines)
    gy=np.abs(np.diff(a.mean(2),axis=0))[:,:-1]; gx=np.abs(np.diff(a.mean(2),axis=1))[:-1,:]
    edge=((gx+gy)>80)
    me=m[:-1,:-1]&edge                          # sharp white = text/line art
    red=(a[...,0]>170)&(a[...,1]<110)&(a[...,2]<90)  # orange-red graphic accent
    r,g,b=a[...,0].mean(),a[...,1].mean(),a[...,2].mean()
    H,W=me.shape
    reg={}
    for name,(y0,y1,x0,x1) in {'tl':(0,.17,0,.42),'tc':(0,.15,.3,.7),'mid':(.15,.85,.15,.85),'bot':(.8,1,0,1)}.items():
        reg[name]=int(me[int(y0*H):int(y1*H),int(x0*W):int(x1*W)].sum())
    ys,xs=np.nonzero(me)
    bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None
    return dict(n=int(me.sum()),wb=int(m.sum()),red=int(red.sum()),bmr=float(b-r),bl=float(b),reg=reg,bbox=bbox)
if __name__=='__main__':
    v=sys.argv[1]; fs=sorted(glob.glob(f'/home/user/ov/f_{v}/*.jpg'))
    with ProcessPoolExecutor(4) as ex: F=list(ex.map(feat,fs,chunksize=64))
    for i,x in enumerate(F): x['t']=i*0.5; x['f']=fs[i]
    json.dump(F,open(f'/home/user/ov/{v}.feat.json','w'))
    n=np.array([x['n'] for x in F]); print(v,len(F),'frames with sharp-white>30:',(n>30).sum(),'>100:',(n>100).sum())
