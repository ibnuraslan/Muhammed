import json
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
for v in ['amy','caylee','noida']:
    I=json.load(open(f'/home/user/ov/{v}.inst.json')); F=json.load(open(f'/home/user/ov/{v}.feat.json'))
    tw,th=320,180;cols=6
    for s in range(0,len(I),36):
        chunk=I[s:s+36]; rows=(len(chunk)+cols-1)//cols
        S=Image.new('RGB',(tw*cols,th*rows)); D=ImageDraw.Draw(S)
        for k,c in enumerate(chunk):
            im=Image.open(F[c['best']]['f']).resize((tw,th)); x=(k%cols)*tw;y=(k//cols)*th; S.paste(im,(x,y))
            lab='%s%d %d:%02d %.0fs'%(v[0],s+k,c['t0']//60,c['t0']%60,c['t1']-c['t0'])
            D.rectangle([x,y+th-20,x+len(lab)*10+6,y+th],fill=(0,0,0)); D.text((x+3,y+th-19),lab,font=font,fill=(255,220,0))
        S.save(f'/home/user/ov/rev_{v}_{s//36}.jpg',quality=80)
