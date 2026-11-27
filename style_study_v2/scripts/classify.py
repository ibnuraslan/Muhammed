import subprocess,numpy as np,json
W,H=214,120
res={}
for v in ['amy','caylee','noida']:
    p=subprocess.run(['ffmpeg','-loglevel','error','-i',f'/home/user/dl/refs/{v}.mp4','-an','-vf',f'fps=1,scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True)
    fr=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W,3).astype(float); n=len(fr)
    r,g,b=fr[...,0].mean((1,2)),fr[...,1].mean((1,2)),fr[...,2].mean((1,2))
    is2d=(b-r<6)&(b<30)          # neutral dark background => 2D graphic / black
    lum=fr.mean(3)
    tl=(lum[:,3:16,3:70]>120).mean((1,2))      # chapter tag top-left
    tc=(lum[:,2:16,85:130]>170).mean((1,2))    # date stamp top-centre
    tag=tl>0.06; date=tc>0.03
    def runs(m):
        out=[];s=None
        for i,x in enumerate(m):
            if x and s is None: s=i
            if not x and s is not None:
                if i-s>=2: out.append((s,i))
                s=None
        return out
    R={'n':n,'2d_frac':float(is2d.mean()),'2d_runs':runs(is2d),'tag_runs':runs(tag),'date_runs':runs(date)}
    res[v]=R
    print(v,'2D/neutral share %.2f'%R['2d_frac'],'2D runs',len(R['2d_runs']),'tag runs',len(R['tag_runs']),'date runs',len(R['date_runs']))
    print('  2D runs:',[(a,b) for a,b in R['2d_runs']][:40])
    print('  tags:',[a for a,b in R['tag_runs']])
    print('  dates:',[a for a,b in R['date_runs']])
json.dump(res,open('/home/user/work/classify.json','w'))
