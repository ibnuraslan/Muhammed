import json,subprocess,wave,numpy as np
# (id, text, gap_after_seconds)
CLIPS=[
 ("a1","In eighteen fifty-one, a man patented an invention,",0.25),
 ("a2","that nobody wanted.",0.45),
 ("b1","Elias Howe, the genius behind the sewing machine, designed it,",0.2),
 ("b2","then simply ignored it.",0.45),
 ("c1","Forty-two years went by.",0.5),
 ("d1","Then another inventor, Whitcomb Judson, improved it,",0.15),
 ("d2","and called it the Clasp Locker.",0.4),
 ("e1","He showed it off at the World's Fair in Chicago.",0.35),
 ("e2","Still,",0.35),
 ("e3","nobody cared.",0.55),
 ("f1","In nineteen thirteen, Gideon Sundback gave it interlocking teeth.",0.45),
 ("g1","Then came World War One.",0.25),
 ("g2","The military needed faster gear.",0.3),
 ("h1","Flight suits.",0.12),
 ("h2","Money belts.",0.12),
 ("h3","Jackets that closed in a second.",0.45),
 ("i1","Suddenly, people noticed.",0.35),
 ("i2","But the moment that changed everything,",0.3),
 ("j1","came in nineteen twenty-three,",0.15),
 ("j2","when a rubber boot company called B. F. Goodrich",0.1),
 ("j3","put them on their boots,",0.3),
 ("k1","and named it after the sound it made.",0.6),
 ("l1","Zip!",0.5),
 ("l2","The zipper.",1.8),
]
LEAD=0.6
SR=22050
out=[np.zeros(int(LEAD*SR),np.int16)]; t=LEAD; cues={}
for cid,text,gap in CLIPS:
    subprocess.run(['python3','-m','piper','-m','../tts/en_US-ryan-high.onnx','-f',f'{cid}.wav','--length-scale','0.96','--',text],check=True,capture_output=True)
    w=wave.open(f'{cid}.wav'); assert w.getframerate()==SR
    a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
    # trim silence
    idx=np.where(np.abs(a)>300)[0]; a=a[max(0,idx[0]-200):idx[-1]+800]
    d=len(a)/SR; cues[cid]={"start":round(t,3),"end":round(t+d,3),"text":text}
    out+= [a,np.zeros(int(gap*SR),np.int16)]; t+=d+gap
v=np.concatenate(out)
with wave.open('vo_full.wav','wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(v.tobytes())
json.dump({"duration":round(t,3),"cues":cues},open('timeline.json','w'),indent=1)
print("total",round(t,2))
for k,c in cues.items(): print(k,c['start'],c['end'])
