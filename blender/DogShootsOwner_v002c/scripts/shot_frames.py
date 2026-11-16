"""render first/last (+mid) frame of every shot. args: out_dir width samples [mode=ends|mid|all3] [only_sids,comma]"""
import bpy, sys, os
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; W=int(a[1]); smp=int(a[2]); mode=a[3] if len(a)>3 else "ends"; only=a[4].split(",") if len(a)>4 and a[4] else None
os.makedirs(out, exist_ok=True)
sc=bpy.context.scene; r=sc.render
r.resolution_x=W; r.resolution_y=round(W*16/9); r.resolution_percentage=100
sc.cycles.samples=smp; sc.cycles.use_denoising=True; r.use_simplify=True; r.simplify_subdivision_render=0
sc.cycles.texture_limit_render='1024'; r.image_settings.file_format='JPEG'
mk=sorted(sc.timeline_markers, key=lambda m:m.frame)
for i,m in enumerate(mk):
    sid=m.name[1:]
    if only and sid not in only: continue
    f0=m.frame; f1=(mk[i+1].frame-1) if i+1<len(mk) else sc.frame_end
    fr={"ends":[f0,f1],"mid":[(f0+f1)//2],"all3":[f0,(f0+f1)//2,f1]}[mode]
    for j,f in enumerate(fr):
        sc.frame_set(f); sc.camera=m.camera
        r.filepath=f"{out}/{i:02d}_{sid}_{j}_f{f:04d}.jpg"; bpy.ops.render.render(write_still=True)
print("DONE")
