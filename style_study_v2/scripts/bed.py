import numpy as np
sr=16000
for v in ['amy','caylee','noida']:
    a=np.fromfile(f'/home/user/work/{v}.f32',np.float32)
    seg=a[:len(a)//4000*4000].reshape(-1,4000)  # 250ms
    rms=20*np.log10(np.sqrt((seg**2).mean(1))+1e-9)
    q=seg[(rms>-40)&(rms<-26)]
    X=np.abs(np.fft.rfft(q*np.hanning(4000),axis=1)).mean(0); f=np.fft.rfftfreq(4000,1/sr)
    bands=[(20,80),(80,250),(250,1000),(1000,4000),(4000,8000)]
    e=[X[(f>=lo)&(f<hi)].sum() for lo,hi in bands]; e=np.array(e)/sum(e)
    # tonality: spectral flatness of pause frames
    P=np.abs(np.fft.rfft(q*np.hanning(4000),axis=1))**2+1e-12
    flat=np.exp(np.log(P[:,5:1000]).mean(1))/P[:,5:1000].mean(1)
    print(v,'pause frames %d (%.0f%%)'%(len(q),100*len(q)/len(seg)),'band shares',dict(zip(['sub','low','mid','himid','hi'],e.round(2))),'median flatness %.3f'%np.median(flat))
