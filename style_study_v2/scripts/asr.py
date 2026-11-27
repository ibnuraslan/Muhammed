import sys,json
from faster_whisper import WhisperModel
v=sys.argv[1]
m=WhisperModel('base.en',device='cpu',compute_type='int8',cpu_threads=1)
import numpy as np
audio=np.fromfile(f'/home/user/work/{v}.f32',np.float32)
segs,_=m.transcribe(audio,language='en',vad_filter=True,beam_size=1)
out=[{'s':s.start,'e':s.end,'t':s.text} for s in segs]
json.dump(out,open(f'/home/user/work/{v}.asr.json','w'))
print('done',v,len(out))
