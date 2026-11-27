import glob,numpy as np
from PIL import Image
for v in ['amy','caylee','noida']:
    px=[]
    for f in glob.glob(f'/home/user/work/fr_{v}/*.jpg'):
        a=np.asarray(Image.open(f).convert('RGB').resize((160,90))).reshape(-1,3).astype(float); px.append(a)
    px=np.concatenate(px)
    br=px.mean(1)
    print(v,'mean RGB',px.mean(0).round(1),'pct pixels luma<20: %.2f'%(br<20).mean())
    # k-means on non-dark pixels
    q=px[br>25]; rng=np.random.default_rng(0); c=q[rng.choice(len(q),6)]
    for _ in range(25):
        l=((q[:,None]-c[None])**2).sum(2).argmin(1); c=np.array([q[l==k].mean(0) if (l==k).any() else c[k] for k in range(6)])
    cnt=np.bincount(l,minlength=6)/len(l); o=np.argsort(-cnt)
    print('  clusters:',['#%02x%02x%02x %.0f%%'%(*c[k].astype(int),cnt[k]*100) for k in o])
    # brightest saturated (accents)
    hsv=np.asarray(Image.fromarray(px.astype(np.uint8)[None]).convert('HSV'))[0].astype(float)
    m=(hsv[:,1]>150)&(hsv[:,2]>150)
    if m.sum():
        h=hsv[m,0]*360/255; hist=np.histogram(h,bins=12,range=(0,360))[0]; print('  saturated-bright hue hist (30deg bins):',hist)
