import json,subprocess,sys,os
from PIL import Image,ImageDraw,ImageFont
v,title=sys.argv[1],sys.argv[2]
J=json.load(open(f'/home/user/work/{v}.cuts.json')); cuts=J['cuts'];dur=J['dur']
b=[0]+cuts+[dur]; shots=[(b[i],b[i+1]) for i in range(len(b)-1) if b[i+1]-b[i]>2.0]
N=24; pick=[shots[round(i*(len(shots)-1)/(N-1))] for i in range(N)]
# ensure hook included: first shot
os.makedirs(f'/home/user/work/fr_{v}',exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
big=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
tw,th=427,240; cols=6; rows=4; hdr=50
S=Image.new('RGB',(tw*cols,th*rows+hdr),(12,12,16)); D=ImageDraw.Draw(S)
D.text((12,10),title,font=big,fill=(235,235,235))
for k,(a,e) in enumerate(pick):
    t=(a+e)/2; fn=f'/home/user/work/fr_{v}/{k:02d}_{t:.1f}.jpg'
    subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',f'/home/user/dl/refs/{v}.mp4','-frames:v','1','-q:v','2',fn,'-y'])
    im=Image.open(fn).resize((tw,th)); x=(k%cols)*tw; y=hdr+(k//cols)*th
    S.paste(im,(x,y)); tc='%d:%02d'%(t//60,t%60)
    D.rectangle([x+4,y+th-28,x+4+len(tc)*12+8,y+th-4],fill=(0,0,0)); D.text((x+8,y+th-27),tc,font=font,fill=(255,210,80))
S.save(f'/home/user/Muhammed/style_study_v2/contact_{v}.jpg',quality=85)
print('ok',len(shots))
