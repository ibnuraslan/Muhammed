import numpy as np,json,sys
for v in ['amy','caylee','noida']:
    d=np.load(f'/home/user/work/{v}.d.npy'); br=np.load(f'/home/user/work/{v}.br.npy')
    c=json.load(open(f'/home/user/work/{v}.cuts.json'))['cuts']
    # dips: local minima of brightness < 35% of surrounding 2s median, separated
    fps=30; dips=[]
    for i in range(30,len(br)-30,3):
        w=np.median(np.concatenate([br[i-30:i-10],br[i+10:i+30]]))
        if br[i]<0.35*w and br[i]<=br[i-3:i+4].min():
            t=i/fps
            if not dips or t-dips[-1]>1.5: dips.append(t)
    # within-shot motion: frames with d<0.0005 => static
    mask=d<0.15
    st=(d[mask]<0.0003).mean()
    print(v,'fade/dip-to-black events',len(dips),'static-frame fraction %.2f'%st,'median intra d %.5f'%np.median(d[mask]))
    json.dump(dips,open(f'/home/user/work/{v}.dips.json','w'))
