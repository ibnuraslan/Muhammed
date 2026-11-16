import json,glob
out=[]
for f in sorted(glob.glob('/tmp/claude-0/b09/bpc/*.json')):
    d=json.load(open(f)); tot={}
    for fr,h in d['frames'].items():
        for k,v in h.items():
            if k.endswith('VIS') and 'Steam' not in k: tot[k]=tot.get(k,0)+1
    fr=sorted({int(x) for x,h in d['frames'].items() if any(k.endswith('VIS') and 'Steam' not in k for k in h)})
    out.append(f"{f.split('/')[-1]}: visible crossing frames (steam volumes excluded) = {len(fr)} {fr[:8]}")
    out += ["   %s x%d" % (k, n) for k, n in sorted(tot.items(), key=lambda x: -x[1])[:8]]
print("\n".join(out)); open('/tmp/claude-0/b09/bpc/summary.txt','w').write("\n".join(out)+"\n")
