import sys,json,numpy as np,subprocess,os
sys.path.insert(0,'/home/user/ov'); from cats import C
from PIL import Image
A=json.load(open('/home/user/ov/anim.json'))
from collections import defaultdict
pos=defaultdict(list); cnt=defaultdict(lambda: defaultdict(int)); dur=defaultdict(list)
for v in ['amy','caylee','noida']:
    I=json.load(open(f'/home/user/ov/{v}.inst.json'))
    for i,c in enumerate(I):
        k=C[(v,i)]
        if k in('dup','skip'): continue
        cnt[k][v]+=1; dur[k].append(c['t1']-c['t0'])
        b=c['bbox']
        if b: pos[k].append(((b[0]+b[2])/2/427,(b[1]+b[3])/2/240,(b[2]-b[0])/427,(b[3]-b[1])/240))
S={}
for k in cnt:
    p=np.array(pos[k]); an=[A[f'{v}:{i}'] for v in ['amy','caylee','noida'] for i in range(200) if C.get((v,i))==k and A.get(f'{v}:{i}')]
    S[k]=dict(count=dict(cnt[k]),dur_med=float(np.median(dur[k])),dur_p10=float(np.percentile(dur[k],10)),dur_p90=float(np.percentile(dur[k],90)),
      cx=float(np.median(p[:,0])),cy=float(np.median(p[:,1])),w=float(np.median(p[:,2])),h=float(np.median(p[:,3])),
      rin=float(np.median([a['rin'] for a in an])) if an else None,rout=float(np.median([a['rout'] for a in an])) if an else None)
    print('%-12s %s dur %.1f (%.1f-%.1f) centre (%.2f,%.2f) size %.2fx%.2f in %s out %s'%(k,dict(cnt[k]),S[k]['dur_med'],S[k]['dur_p10'],S[k]['dur_p90'],S[k]['cx'],S[k]['cy'],S[k]['w'],S[k]['h'],S[k]['rin'],S[k]['rout']))
json.dump(S,open('/home/user/ov/stats.json','w'))
# example crops
EX={'date':[('amy',1),('noida',14),('amy',21),('noida',72)],
'quote':[('caylee',72),('caylee',77),('amy',40),('noida',30),('amy',11),('caylee',39)],
'keyword':[('amy',39),('amy',86),('noida',45),('caylee',67)],
'section_tag':[('noida',23),('caylee',37),('amy',30),('noida',4)],
'title':[('caylee',2),('noida',2),('amy',26),('amy',103)],
'whos_who':[('amy',58),('amy',59),('caylee',6),('noida',27)],
'place':[('caylee',36),('noida',15),('amy',52),('caylee',5)],
'line_art':[('amy',4),('amy',9),('caylee',12),('noida',10)],
'family_tree':[('amy',3),('caylee',8),('noida',6)],
'map':[('amy',12),('caylee',4),('noida',7),('noida',8)],
'document':[('noida',29),('noida',41),('caylee',16),('noida',77)],
'arrows':[('amy',37),('amy',38),('noida',36)],
'bookends':[('amy',0),('amy',106),('caylee',88),('amy',107)],
'sponsor':[('caylee',19),('caylee',21)]}
FULL={'line_art','family_tree','map','document','bookends','sponsor','title','place'}
os.makedirs('/home/user/ov/ex',exist_ok=True)
for k,L in EX.items():
    for v,i in L:
        c=json.load(open(f'/home/user/ov/{v}.inst.json'))[i]; F=json.load(open(f'/home/user/ov/{v}.feat.json'))
        t=F[c['best']]['t']+0.25; fn=f'/home/user/ov/ex/{k}_{v}_{i}.png'
        subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',f'/home/user/dl/refs/{v}.mp4','-frames:v','1',fn,'-y'])
        im=Image.open(fn)
        if k not in FULL and c['bbox']:
            b=[x*2 for x in c['bbox']]; cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2; w=max(b[2]-b[0]+60,260); h=max(b[3]-b[1]+50,110)
            x0=int(max(0,min(854-w,cx-w/2))); y0=int(max(0,min(480-h,cy-h/2)))
            im=im.crop((x0,y0,int(x0+w),int(y0+h)))
        im.save(fn)
