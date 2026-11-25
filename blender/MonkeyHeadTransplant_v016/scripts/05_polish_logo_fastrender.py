"""polish.py -- CFG.json OUT.blend : logo print + fast-render settings + purge + pack (look-neutral)."""
import bpy, sys, json, os
a=sys.argv[sys.argv.index("--")+1:]; cfg=json.load(open(a[0])); out=a[1]
sc=bpy.context.scene; r=sc.render; c=sc.cycles
log=[]
# ---------- logo print on a mesh via a planar UV + front mask ----------
def add_logo(L):
    img=bpy.data.images.load(L["image"],check_existing=True); img.pack()
    img.alpha_mode='STRAIGHT'
    ob=bpy.data.objects[L["object"]]; me=ob.data
    ax={"x":0,"y":1,"z":2}; ua,va,fa=ax[L["u_axis"]],ax[L["v_axis"]],ax[L["front_axis"]]
    uv=me.uv_layers.new(name="LogoUV"); 
    mask=me.color_attributes.new(name="LogoMask",type='FLOAT_COLOR',domain='POINT')
    cu,cv,W=L["cu"],L["cv"],L["w"]; H=L.get("h",W*img.size[1]/img.size[0])
    fs=L["front_sign"]; flip=L.get("u_flip",1)
    nfront=0
    for v in me.vertices:
        front = (v.normal[fa]*fs > L.get("normal_min",0.5)) and (v.co[fa]*fs > L.get("front_min",-9))
        mask.data[v.index].color=(1.0,1.0,1.0,1.0) if front else (0,0,0,1)
        nfront+=front
    for loop in me.loops:
        co=me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=(flip*(co[ua]-cu)/W+0.5,(co[va]-cv)/H+0.5)
    me.uv_layers.active_index=0
    for i,u in enumerate(me.uv_layers): 
        if u.name!="LogoUV": u.active_render=True; break
    mats=[s.material for s in ob.material_slots if s.material]
    mat=mats[L.get("slot",0)]
    if mat.users>1: mat=mat.copy(); ob.material_slots[L.get("slot",0)].material=mat
    nt=mat.node_tree; bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    uvn=nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map="LogoUV"
    tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=img; tx.extension='CLIP'; tx.interpolation='Cubic'
    nt.links.new(uvn.outputs['UV'],tx.inputs['Vector'])
    at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name="LogoMask"
    mul=nt.nodes.new('ShaderNodeMath'); mul.operation='MULTIPLY'
    nt.links.new(tx.outputs['Alpha'],mul.inputs[0]); nt.links.new(at.outputs['Fac'],mul.inputs[1])
    mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'
    bc=bs.inputs['Base Color']
    if bc.links: nt.links.new(bc.links[0].from_socket,mix.inputs[6])
    else: mix.inputs[6].default_value=bc.default_value
    nt.links.new(tx.outputs['Color'],mix.inputs[7]); nt.links.new(mul.outputs[0],mix.inputs['Factor'])
    nt.links.new(mix.outputs[2],bc)
    log.append(f"logo on {ob.name} mat {mat.name} front verts {nfront} size {W:.3f}x{H:.3f} m")
for L in cfg.get("logos",[]): add_logo(L)

def add_decal(D):
    import bmesh, mathutils
    img=bpy.data.images.load(D["image"],check_existing=True); img.pack(); img.alpha_mode='STRAIGHT'
    host=bpy.data.objects[D["object"]]
    dg=bpy.context.evaluated_depsgraph_get(); ev=host.evaluated_get(dg); em=ev.to_mesh()
    mn=[min(v.co[i] for v in em.vertices) for i in range(3)]; mx=[max(v.co[i] for v in em.vertices) for i in range(3)]
    ev.to_mesh_clear()
    W=D["w"]; H=W*img.size[1]/img.size[0]
    mat=bpy.data.materials.get("M_DaKrasDecal_"+img.name.split('.')[0])
    if mat is None:
        mat=bpy.data.materials.new("M_DaKrasDecal_"+img.name.split('.')[0]); mat.use_nodes=True
        nt=mat.node_tree; bs=nt.nodes["Principled BSDF"]; tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=img; tx.interpolation='Cubic'
        nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
        bs.inputs['Roughness'].default_value=D.get("rough",0.6)
        try: mat.surface_render_method='DITHERED'
        except Exception: pass
    for side in D["sides"]:
        ax="xyz".index(side[1]); sg=-1 if side[0]=='-' else 1
        me=bpy.data.meshes.new("DaKrasDecal_"+host.name+side); bm=bmesh.new(); uvl=bm.loops.layers.uv.new("UVMap")
        cz=D.get("cz",(mn[2]+mx[2])/2); cu=D.get("cu",0.0)
        off=(mx[ax] if sg>0 else mn[ax])+sg*D.get("gap",0.0015)
        # in-plane horizontal axis: viewer facing the side sees +u to their right
        hax=0 if ax==1 else 1
        hs = (-1 if sg>0 else 1) if ax==1 else (1 if sg>0 else -1)
        vs=[]
        for (du,dv) in ((-0.5,-0.5),(0.5,-0.5),(0.5,0.5),(-0.5,0.5)):
            co=[0.0,0.0,0.0]; co[ax]=off; co[hax]=hs*(cu+du*W); co[2]=cz+dv*H; vs.append(bm.verts.new(co))
        f=bm.faces.new(vs)
        for lp,(u,v) in zip(f.loops,((0,0),(1,0),(1,1),(0,1))): lp[uvl].uv=(u,v)
        f.normal_update()
        if (f.normal[ax]*sg)<0: f.normal_flip()
        bm.to_mesh(me); bm.free()
        o=bpy.data.objects.new(me.name,me); o.data.materials.append(mat)
        for c in host.users_collection: c.objects.link(o)
        o.parent=host; o.matrix_parent_inverse=mathutils.Matrix.Identity(4)
        o.visible_shadow=False
        ad=host.animation_data
        if ad and ad.action:
            from bpy_extras import anim_utils
            cb=anim_utils.action_get_channelbag_for_slot(ad.action,ad.action_slot)
            for fc in cb.fcurves:
                if fc.data_path in ("hide_render","hide_viewport"):
                    for k in fc.keyframe_points:
                        setattr(o,fc.data_path,bool(k.co[1])); o.keyframe_insert(fc.data_path,frame=k.co[0])
                    log.append(f"copied {fc.data_path} keys {[(int(k.co[0]),int(k.co[1])) for k in fc.keyframe_points]}")
            o.hide_render=host.hide_render; o.hide_viewport=host.hide_viewport
        log.append(f"decal {o.name} on {host.name} side {side} {W:.3f}x{H:.3f} m at {off:.4f}")
for D in cfg.get("decals",[]): add_decal(D)
# ---------- fast-render settings (look-neutral) ----------
c.use_adaptive_sampling=True
if not (0.03<=c.adaptive_threshold<=0.05): c.adaptive_threshold=0.05
if c.samples>64: c.samples=64
c.use_denoising=True; c.denoiser='OPENIMAGEDENOISE'; c.denoising_input_passes='RGB_ALBEDO_NORMAL'
c.max_bounces=min(c.max_bounces,6); c.diffuse_bounces=min(c.diffuse_bounces,3); c.glossy_bounces=min(c.glossy_bounces,3)
c.transmission_bounces=min(c.transmission_bounces,6)
if not cfg.get('keep_transparent'): c.transparent_max_bounces=max(8,min(c.transparent_max_bounces,16))
c.caustics_reflective=False; c.caustics_refractive=False
r.use_persistent_data=True
r.use_simplify=True; c.texture_limit_render='2048'; r.simplify_child_particles_render=min(r.simplify_child_particles_render,1.0)
maxlv=max([m.render_levels for o in bpy.data.objects for m in getattr(o,'modifiers',[]) if m.type=='SUBSURF']+[1])
r.simplify_subdivision_render=min(2,maxlv)
# ---------- delete hidden, never-animated, unreferenced objects; purge orphans ----------
refs=set()
for o in bpy.data.objects:
    if o.parent: refs.add(o.parent.name)
    for con in getattr(o,'constraints',[]):
        t=getattr(con,'target',None); refs.add(t.name if t else None)
    for m in getattr(o,'modifiers',[]):
        for at_ in ('object','target','offset_object','mirror_object'):
            t=getattr(m,at_,None)
            if isinstance(t,bpy.types.Object): refs.add(t.name)
dele=[] if cfg.get('no_delete') else [o.name for o in bpy.data.objects if o.hide_render and o.animation_data is None and not o.children and o.name not in refs and o.type in ('MESH','CURVE')]
for n in dele: bpy.data.objects.remove(bpy.data.objects[n])
log.append(f"deleted hidden unused objects {dele}")
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
# ---------- output + VO ----------
r.filepath=cfg["out_path"]
for s in bpy.data.sounds:
    if s.packed_file is None: s.pack()
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.use_file_compression=True
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True,relative_remap=True)
print("POLISH_LOG", json.dumps(log))
