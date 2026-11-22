import sys,json,numpy as np,soundfile as sf
x,sr=sf.read(sys.argv[1]); t=json.load(open(sys.argv[2]))
if not isinstance(next(iter(t.values())),dict):
    st=0;t2={}
    for k,v in t.items(): n=round(v*24); t2[k]={'start':st,'frames':n}; st+=n
    t=t2
out=[]
for k,v in t.items():
    a=int(v['start']/24*sr); b=int((v['start']+v['frames'])/24*sr); s=x[a:b]
    out.append(f"{k}:{20*np.log10(np.sqrt(np.mean(s**2))+1e-9):.0f}")
print(' '.join(out))
