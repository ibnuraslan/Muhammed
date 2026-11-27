import sys,subprocess,numpy as np,json
v=sys.argv[1]; W,H=64,36
p=subprocess.Popen(['ffmpeg','-loglevel','error','-i',f'/home/user/dl/refs/{v}.mp4','-an','-vf',f'scale={W}:{H},format=gray','-f','rawvideo','-'],stdout=subprocess.PIPE)
fr=np.frombuffer(p.stdout.read(),np.uint8).reshape(-1,H,W).astype(np.float32)
n=len(fr); fps=30.0
m=fr.reshape(n,-1); m=m-m.mean(1,keepdims=True); nr=np.linalg.norm(m,axis=1)+1e-3
corr=(m[1:]*m[:-1]).sum(1)/(nr[1:]*nr[:-1])
d=1-corr  # dissimilarity
br=fr.mean((1,2))
np.save(f'/home/user/work/{v}.d.npy',d); np.save(f'/home/user/work/{v}.br.npy',br)
cuts=[]
for i in range(1,len(d)-1):
    lo=max(0,i-10);hi=min(len(d),i+11)
    nb=np.concatenate([d[lo:i],d[i+1:hi]])
    if d[i]>0.15 and d[i]>=nb.max() and d[i]>5*np.median(nb)+0.05:
        t=(i+1)/fps
        if not cuts or t-cuts[-1]>0.5: cuts.append(t)
# fades to/through black: brightness dips
dur=n/fps
json.dump({'dur':dur,'cuts':cuts},open(f'/home/user/work/{v}.cuts.json','w'))
c=np.array(cuts); shots=np.diff(np.concatenate([[0],c,[dur]]))
print(v,'dur %.0f cuts %d cpm %.1f ASL %.1f median %.1f p10 %.1f p90 %.1f'%(dur,len(c),len(c)/dur*60,shots.mean(),np.median(shots),*np.percentile(shots,[10,90])))
for a,b in [(0,15),(0,60),(60,180),(180,600),(600,dur)]:
    k=((c>=a)&(c<b)).sum(); print('  %d-%d s: %d cuts (%.1f/min)'%(a,b,k,k/(min(b,dur)-a)*60))
print('  600-720:',[round(x,1) for x in c if 600<=x<720])
print('  0-60:',[round(x,1) for x in c if x<60])
dark=(br<6).mean(); print('  frac near-black frames %.3f, mean luma %.1f'%(dark,br.mean()))
