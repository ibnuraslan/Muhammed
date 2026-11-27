"""WW1Assassination v009: farm render settings (render time <= 120 s/frame on a 4-core CPU at 1080x1920; measured 63-107 s).
blender -b slim.blend --python 05_farm_settings.py -- <out.blend>     (then pipeline/package_for_farm.py)
28 adaptive samples (threshold 0.06) + OIDN denoise, 4 bounces (diffuse/glossy 2, transparent 8), 1K texture limit,
subdivision render level 1, and no light-sampling of the weak emissive materials (lamp glass, logo, map fire band);
the muzzle flashes and the fireball keep emission sampling. Side by side with 64 samples there is no visible difference."""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; r = sc.render; c = sc.cycles
c.samples = 28; c.adaptive_threshold = 0.06; c.use_adaptive_sampling = True; c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transparent_max_bounces = 8
c.texture_limit_render = '1024'; r.use_simplify = True; r.simplify_subdivision_render = 1
for m in bpy.data.materials:
    if m.node_tree and not m.name.startswith(("M_MuzzleFlash", "M_Fireball")):
        for nd in m.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED' and (nd.inputs["Emission Strength"].default_value > 0 or nd.inputs["Emission Strength"].is_linked):
                m.cycles.emission_sampling = 'NONE'; print("NO_EMISSION_SAMPLING", m.name); break
bpy.ops.wm.save_as_mainfile(filepath=out)
print("FARM_SETTINGS_DONE")
