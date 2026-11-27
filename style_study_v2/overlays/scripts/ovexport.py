import sys,json,subprocess,os,numpy as np
sys.path.insert(0,'/home/user/ov'); from cats import C
from PIL import Image,ImageDraw,ImageFont
OUT='/home/user/Muhammed/style_study_v2/overlays/'
NAMES={'date':'date_time_stamps','quote':'quote_cards','place':'place_object_labels','section_tag':'section_tags','title':'title_chapter_cards','whos_who':'name_labels_whos_who','line_art':'line_art_illustrations','family_tree':'family_tree_boards','map':'maps','document':'documents_records_timelines','arrows':'arrows_highlights','bookends':'disclaimer_end_cards','sponsor':'sponsor_segment'}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17)
big=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
TITLES={'amy':'Amy Bradley','caylee':'Caylee Anthony','noida':'Noida Double Murder'}
index=[]
for v in ['amy','caylee','noida']:
    I=json.load(open(f'/home/user/ov/{v}.inst.json')); F=json.load(open(f'/home/user/ov/{v}.feat.json'))
    items=[]
    for i,c in enumerate(I):
        cat=C[(v,i)]
        if cat in('dup','skip'): continue
        t=F[c['best']]['t']+0.25
        tc='%02d-%02d'%(t//60,t%60)
        d=OUT+NAMES[cat]; os.makedirs(d,exist_ok=True)
        fn=f'{d}/{v}_{tc}_{i:03d}.jpg'
        subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',f'/home/user/dl/refs/{v}.mp4','-frames:v','1','-q:v','2',fn,'-y'])
        items.append((t,cat,fn)); index.append(dict(video=v,inst=i,category=NAMES[cat],time_s=round(t,2),on_screen_s=round(c['t1']-c['t0'],1),file=fn.replace('/home/user/Muhammed/style_study_v2/overlays/','')))
    # contact sheet(s)
    cols=7;tw,th=366,206;per=56
    for p,s in enumerate(range(0,len(items),per)):
        ch=items[s:s+per]; rows=(len(ch)+cols-1)//cols; hdr=46
        S=Image.new('RGB',(cols*tw,rows*th+hdr),(14,14,18)); D=ImageDraw.Draw(S)
        D.text((10,9),f'{TITLES[v]}: on-screen text & graphics ({len(items)} instances){"  page %d"%(p+1) if len(items)>per else ""}',font=big,fill=(240,240,240))
        for k,(t,cat,fn) in enumerate(ch):
            im=Image.open(fn).resize((tw,th)); x=(k%cols)*tw;y=hdr+(k//cols)*th; S.paste(im,(x,y))
            lab='%d:%02d  %s'%(t//60,t%60,NAMES[cat].replace('_',' '))
            D.rectangle([x,y+th-22,x+len(lab)*10.5+8,y+th],fill=(0,0,0)); D.text((x+4,y+th-21),lab,font=font,fill=(255,210,80))
        S.save(OUT+f'sheet_{v}{"_%d"%(p+1) if len(items)>per else ""}.jpg',quality=82)
    print(v,len(items))
json.dump(index,open(OUT+'index.json','w'),indent=0)
