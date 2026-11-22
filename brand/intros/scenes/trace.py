import cv2, numpy as np, json, sys
im = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
h, w = im.shape[:2]
a = im[:,:,3]
b,g,r = im[:,:,0].astype(int), im[:,:,1].astype(int), im[:,:,2].astype(int)
fill = ((a>128) & (g>150) & (r>150) & (b<120)).astype(np.uint8)*255
sil = (a>128).astype(np.uint8)*255
out = {}
for name, m in (("sil", sil), ("fill", fill)):
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cs:
        if cv2.contourArea(c) < 30: continue
        c = cv2.approxPolyDP(c, 0.8, True)[:,0,:]
        # normalise: width 1 => x in [-0.5,0.5]
        polys.append([[(x - w/2)/w, (h/2 - y)/w] for x,y in c.tolist()])
    out[name] = polys
    print(name, len(polys), sum(len(p) for p in polys))
out["aspect"] = w/h
json.dump(out, open(sys.argv[2], "w"))
