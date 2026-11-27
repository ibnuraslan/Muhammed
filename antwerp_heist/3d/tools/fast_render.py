"""Cheap self-render version of a shot (speed test). The original .blend is never modified.

    blender -b shots/P1/S14.blend --python tools/fast_render.py -- OUTDIR [frames|still F]
Settings: 960x540 (upscale to 1080p in ffmpeg), Cycles SPP (env, default 20) adaptive + OIDN, 4 bounces
(diffuse 2 / glossy 2 / transmission 2 / volume 0), no caustics, clamp indirect 5, persistent data, textures 1K,
volumes replaced by a compositor depth fog (+ optional sun-beam glare)."""
import bpy, os, sys, time
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0]); MODE = argv[1] if len(argv) > 1 else "frames"
os.makedirs(OUT, exist_ok=True)
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene; c = sc.cycles; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 960, 540, 100
c.samples = int(E("SPP", 20)); c.use_adaptive_sampling = True; c.adaptive_threshold = E("ADAPT", 0.03)
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
try:
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'; c.denoising_prefilter = 'ACCURATE'
except Exception:
    pass
c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 2; c.volume_bounces = 0
c.transparent_max_bounces = 8
c.caustics_reflective = False; c.caustics_refractive = False; c.blur_glossy = 1.0
c.sample_clamp_direct = 0.0; c.sample_clamp_indirect = 5.0
c.light_sampling_threshold = 0.05
r.use_persistent_data = True
r.use_simplify = True; c.texture_limit_render = '1024'
r.use_motion_blur = bool(int(E("MB", 0)))
# --- volumes out, cheap fakes in -----------------------------------------------------------------------------
vols = []
for o in bpy.data.objects:
    for s in o.material_slots:
        m = s.material
        out = m and m.node_tree and next((n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out and out.inputs['Volume'].is_linked and not out.inputs['Surface'].is_linked:
            vols.append(o)
for o in set(vols):
    o.hide_render = True; print("VOLUME OFF", o.name)
sc.view_layers[0].use_pass_z = True
nt = sc.compositing_node_group; N = nt.nodes; L = nt.links
rl = next(n for n in N if n.bl_idname == "CompositorNodeRLayers")
first = next(l for l in L if l.from_node == rl and l.from_socket.name == "Image")
dst = first.to_socket; L.remove(first)
dens = E("FOG", 0.06)                               # fog factor = 1 - exp(-dens * depth)
m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = -dens
m2 = N.new("ShaderNodeMath"); m2.operation = 'EXPONENT'
m3 = N.new("ShaderNodeMath"); m3.operation = 'SUBTRACT'; m3.inputs[0].default_value = 1.0
L.new(rl.outputs["Depth"], m1.inputs[0]); L.new(m1.outputs[0], m2.inputs[0]); L.new(m2.outputs[0], m3.inputs[1])
fog = N.new("ShaderNodeMix"); fog.data_type = 'RGBA'; fog.blend_type = 'SCREEN'
hz = [E("FOG_R", 0.62), E("FOG_G", 0.50), E("FOG_B", 0.36)]
fog.inputs[7].default_value = (*hz, 1.0)
L.new(m3.outputs[0], fog.inputs[0]); L.new(rl.outputs["Image"], fog.inputs[6])
last = fog.outputs[2]
if E("BEAMS", 0) > 0:                                # light-shaft fake: sun-beam glare from the bright window
    g = N.new("CompositorNodeGlare")
    g.inputs["Type"].default_value = "Sun Beams"
    g.inputs["Quality"].default_value = "High"
    g.inputs["Strength"].default_value = E("BEAMS", 0.3)
    g.inputs["Threshold"].default_value = E("BTH", 0.8)
    g.inputs["Size"].default_value = E("BSIZE", 0.5)
    g.inputs["Sun Position"].default_value = (E("BX", 0.75), E("BY", 0.8))
    L.new(last, g.inputs[0]); last = g.outputs[0]
L.new(last, dst)
r.image_settings.file_format = 'PNG'
if MODE == "still":
    f = int(argv[2]); sc.frame_set(f); r.filepath = os.path.join(OUT, "fast_%04d.png" % f)
    t = time.time(); bpy.ops.render.render(write_still=True); print("FAST_S", f, round(time.time() - t, 1))
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "S14_fast.blend"), compress=True, relative_remap=True, copy=True)
    times = []; t = time.time()
    def done(scene, *a):
        global t
        times.append(time.time() - t); print("FRAME", scene.frame_current, round(times[-1], 1), flush=True); t = time.time()
    bpy.app.handlers.render_post.append(done)
    r.filepath = os.path.join(OUT, "frames", "")
    t = time.time(); bpy.ops.render.render(animation=True)
    print("AVG_S", round(sum(times) / len(times), 1), "FIRST", round(times[0], 1), "REST", round(sum(times[1:]) / max(1, len(times) - 1), 1))
