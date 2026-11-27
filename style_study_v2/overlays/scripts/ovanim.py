import sys,json,subprocess,numpy as np
sys.path.insert(0,'/home/user/ov'); from cats import C
from concurrent.futures import ProcessPoolExecutor
W,H=427,240
def mask(a):
    a=a.astype(np.int16); mn=a.min(2); mx=a.max(2)
    m=(mn>150)&(mx-mn<45)
    g=a.mean(2); e=np.zeros_like(m); e[:-1,:-1]=(np.abs(np.diff(g,axis=0))[:,:-1]+np.abs(np.diff(g,axis=1))[:-1,:])>80
    return m&e
def job(args):
    v,i,c=args
    t0=max(0,c['t0']-1.5); dur=c['t1']-c['t0']+3.0
    p=subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t0),'-t',str(dur),'-i',f'/home/user/dl/refs/{v}.mp4','-an','-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True)
    fr=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W,3)
    bb=c['bbox']; x0,y0,x1,y1=max(0,bb[0]-6),max(0,bb[1]-6),min(W,bb[2]+7),min(H,bb[3]+7)
    cnt=[];cx=[];ext=[]
    for f in fr:
        m=mask(f[y0:y1,x0:x1]); cnt.append(m.sum())
        ys,xs=np.nonzero(m); cx.append(xs.mean() if len(xs) else np.nan); ext.append(xs.max()-xs.min() if len(xs)>5 else 0)
    cnt=np.array(cnt,float); 
    if cnt.max()<10: return (v,i,None)
    n=cnt/cnt.max(); fps=30
    on=np.nonzero(n>0.5)[0]; a,b=on[0],on[-1]
    # rise: from last <0.1 before a to first >0.9
    pre=np.nonzero(n[:a]<0.1)[0]; s=pre[-1] if len(pre) else 0
    hi=np.nonzero(n>0.9)[0]; f9=hi[0]; l9=hi[-1]
    post=np.nonzero(n[b:]<0.1)[0]; e=b+post[0] if len(post) else len(n)-1
    rin=(f9-s)/fps; rout=(e-l9)/fps; hold=(l9-f9)/fps; total=(e-s)/fps
    # motion during rise
    seg=[k for k in range(s,f9+1) if not np.isnan(cx[k])]
    dx=(cx[seg[-1]]-cx[seg[0]]) if len(seg)>1 else 0
    grow=(ext[f9]-ext[seg[0]])/max(ext[f9],1) if seg else 0
    return (v,i,dict(rin=round(rin,2),rout=round(rout,2),hold=round(hold,2),total=round(total,2),dx=round(float(dx),1),grow=round(float(grow),2)))
if __name__=='__main__':
    jobs=[]
    for v in ['amy','caylee','noida']:
        I=json.load(open(f'/home/user/ov/{v}.inst.json'))
        for i,c in enumerate(I):
            if C[(v,i)] not in('dup','skip','sponsor') and c['bbox']: jobs.append((v,i,c))
    with ProcessPoolExecutor(4) as ex: R=list(ex.map(job,jobs))
    out={f'{v}:{i}':r for v,i,r in R}
    json.dump(out,open('/home/user/ov/anim.json','w'))
    from collections import defaultdict
    agg=defaultdict(list)
    for v,i,r in R:
        if r: agg[C[(v,i)]].append(r)
    for k,L in agg.items():
        f=lambda key: np.median([x[key] for x in L])
        print('%-12s n=%2d in %.2fs out %.2fs hold %.1fs total %.1fs | |dx|>8: %d  grow>0.4: %d'%(k,len(L),f('rin'),f('rout'),f('hold'),f('total'),sum(abs(x['dx'])>8 for x in L),sum(x['grow']>0.4 for x in L)))
