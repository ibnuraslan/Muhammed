# exec'd by 02_build.py: look, render settings, logo, library hidden.
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "//render/BalconyToddler_"
bpy.data.collections["PROPS"].hide_render = True
for o in bpy.data.collections["PROPS"].objects: o.hide_render = o.hide_viewport = True
if bpy.data.collections.get("PROXY"):
    bpy.data.collections["PROXY"].hide_render = True
    for o in bpy.data.collections["PROXY"].objects: o.hide_render = o.hide_viewport = True
# DA KRAS FILMS on the cafe sign across the street (white board, dark logo): seen behind the running man in shot 11,
# never in the close shots of the boy
LOGO = logo_decal("Logo_CafeSign", (-2.4, -16.374, 3.0), (R_(90), 0, R_(180)), 1.85, True, CS)
LOGO.parent = OSIGN; LOGO.matrix_parent_inverse = OSIGN.matrix_world.inverted()
# the apartment door stands open (grandma comes in through it)
DHINGE.rotation_euler = (0, 0, R_(-100))
