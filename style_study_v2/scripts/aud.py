import numpy as np,sys
sr=16000
for v in ['amy','caylee','noida']:
    a=np.fromfile(f'/home/user/work/{v}.f32',np.float32)
    n=len(a)//sr*sr; x=a[:n].reshape(-1,sr//10)  # 100ms frames
    rms=20*np.log10(np.sqrt((x**2).mean(1))+1e-9)
    # spectral: per 100ms frame low band energy (<200Hz) share
    X=np.abs(np.fft.rfft(x*np.hanning(x.shape[1]),axis=1)); f=np.fft.rfftfreq(x.shape[1],1/sr)
    low=X[:,f<200].sum(1)/X.sum(1)
    q=np.percentile(rms,[5,25,50,75,95])
    # quiet floor: frames that are pauses (bottom 15%) — level tells whether a bed runs under
    floor=np.percentile(rms,10)
    silent=(rms<-55).mean()
    # onsets: jumps > 10 dB within 100 ms
    on=((rms[1:]-rms[:-1])>10).sum()/ (n/sr/60)
    print(v,'rms pct5/25/50/75/95',q.round(1),'floor10 %.1f dB'%floor,'digital-silence frac %.3f'%silent,'onsets>10dB/min %.1f'%on)
    print('   first 15s rms per s:',[round(float(r),0) for r in rms[:150].reshape(15,10).mean(1)])
