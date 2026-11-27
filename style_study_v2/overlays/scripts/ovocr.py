import sys,json,numpy as np,pytesseract
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
def ocr(f):
    a=np.asarray(Image.open(f).convert('RGB')).astype(np.int16)
    mn=a.min(2);mx=a.max(2)
    m=((mn>140)&(mx-mn<60))
    im=Image.fromarray(np.where(m,0,255).astype(np.uint8)).resize((a.shape[1]*2,a.shape[0]*2))
    d=pytesseract.image_to_data(im,config='--psm 11',output_type=pytesseract.Output.DICT)
    words=[]
    for i,w in enumerate(d['text']):
        w=w.strip()
        if w and float(d['conf'][i])>55 and sum(c.isalnum() for c in w)>=2:
            words.append([w,d['left'][i]//2,d['top'][i]//2,d['width'][i]//2,d['height'][i]//2,float(d['conf'][i])])
    return words
if __name__=='__main__':
    v=sys.argv[1]; F=json.load(open(f'/home/user/ov/{v}.feat.json'))
    idx=[i for i,x in enumerate(F) if x['n']>30 or (x['bmr']<6 and x['bl']<30 and x['wb']>50)]
    with ProcessPoolExecutor(4) as ex: R=list(ex.map(ocr,[F[i]['f'] for i in idx],chunksize=8))
    out={i:r for i,r in zip(idx,R)}
    json.dump(out,open(f'/home/user/ov/{v}.ocr.json','w')); print(v,len(idx),'ocr; with words:',sum(1 for r in R if r))
