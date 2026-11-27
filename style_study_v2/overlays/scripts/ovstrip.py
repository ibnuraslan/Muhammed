import json,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',13)
picks=[('amy',1,'date'),('caylee',72,'quote'),('noida',23,'section_tag'),('amy',26,'title'),('noida',8,'map'),('caylee',7,'family_tree'),('amy',58,'whos_who'),('amy',37,'arrows'),('noida',29,'document'),('caylee',2,'title_ep')]
rows=[]
for v,i,cat in picks:
    c=json.load(open(f'/home/user/ov/{v}.inst.json'))[i]; bb=c['bbox']
    x0,y0,x1,y1=[int(k*2) for k in (max(0,bb[0]-10),max(0,bb[1]-10),min(427,bb[2]+10),min(240,bb[3]+10))]
    t0=max(0,c['t0']-0.6)
    fs=[]
    for k in range(12):
        t=t0+k*0.2
        p=subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',f'/home/user/dl/refs/{v}.mp4','-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True)
        import io; im=Image.open(io.BytesIO(p.stdout)).crop((x0,y0,x1,y1)); im.thumbnail((200,120)); fs.append((t,im))
    R=Image.new('RGB',(200*12+150,125),(30,30,30)); D=ImageDraw.Draw(R); D.text((4,50),f'{cat}\n{v}{i}',font=font,fill='yellow')
    for k,(t,im) in enumerate(fs): R.paste(im,(150+k*200,0)); D.text((152+k*200,110),'%.1f'%t,font=font,fill='white')
    rows.append(R)
S=Image.new('RGB',(rows[0].width,125*len(rows)))
for k,r in enumerate(rows): S.paste(r,(0,k*125))
S.save('/home/user/ov/strips.jpg',quality=85)
