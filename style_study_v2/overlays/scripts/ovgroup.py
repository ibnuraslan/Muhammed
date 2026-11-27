import json,numpy as np,sys
for v in ['amy','caylee','noida']:
    F=json.load(open(f'/home/user/ov/{v}.feat.json'))
    cuts=np.array(json.load(open(f'/home/user/work/{v}.cuts.json'))['cuts'])
    cand=[x['n']>30 or (x['bmr']<6 and x['bl']<30 and x['wb']>50) for x in F]
    inst=[];cur=None
    def iou(a,b):
        if a is None or b is None: return 0
        ix=max(0,min(a[2],b[2])-max(a[0],b[0]));iy=max(0,min(a[3],b[3])-max(a[1],b[1]))
        u=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-ix*iy
        return ix*iy/u if u>0 else 0
    for i,x in enumerate(F):
        if not cand[i]:
            if cur and i-cur['last']>2: inst.append(cur);cur=None
            continue
        if cur:
            cut_between=((cuts>F[cur['last']]['t'])&(cuts<=x['t'])).any()
            # same instance if close in time, no cut, overlapping bbox
            if i-cur['last']<=2 and not cut_between and iou(F[cur['last']]['bbox'],x['bbox'])>0.3:
                cur['last']=i;cur['frames'].append(i);continue
            inst.append(cur)
        cur={'first':i,'last':i,'frames':[i]}
    if cur: inst.append(cur)
    inst=[c for c in inst if len(c['frames'])>=2]   # on screen >=1s
    for c in inst:
        best=max(c['frames'],key=lambda k:F[k]['n']); c['best']=best; c['t0']=F[c['first']]['t']; c['t1']=F[c['last']]['t']+0.5
        c['bmr']=F[best]['bmr']; c['reg']=F[best]['reg']; c['bbox']=F[best]['bbox']
    json.dump(inst,open(f'/home/user/ov/{v}.inst.json','w'))
    print(v,len(inst),'instances; durations median %.1fs'%np.median([c['t1']-c['t0'] for c in inst]))
