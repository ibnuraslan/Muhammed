# DwarfGiant — Connect26

Vertical true-story short (1080×1920, 60 fps, frames 1–2340 = 39.0 s). One continuous camera (`CAM_Film`), no cuts.

## Build (from this folder)
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --python scripts/01_build_people.py -- people.blend                 # MPFB2 cast (needs the MPFB extension)
$B -b people.blend --python scripts/02_scene.py -- <assets_dir> scene.blend  # sets + CC-BY/CC0 assets
$B -b scene.blend --python scripts/03_anim.py -- ../pipeline film.blend      # animation, cutaways, camera
$B -b film.blend --python scripts/03c_hands.py -- film_h.blend            # Limit Rotation on fingers/thumb/wrist, elbow IK limits, relaxed curl
$B -b film_h.blend --python scripts/03d_props.py -- <assets_dir> film_p.blend  # officer caps, surgeon caps/masks, drape, blanket, OR lamp
$B -b film_p.blend --python ../pipeline/anim_look.py -- film_l.blend --no-sky   # animated-CG look pass (client 22:45)
$B -b film_l.blend --python scripts/04b_hand_audit.py -- review/C_hand_audit.txt 2   # BVH hand audit every 2 frames
$B -b film_l.blend --python scripts/05_package_prep.py -- <out.blend>        # shrink textures, farm settings
```
Assets come from `pipeline/find_models.py` (Sketchfab/Objaverse CC-BY) and `pipeline/fetch_polyhaven.py` (CC0); see CREDITS.md.

## Staging
- Office 1917 (x −3.5…3.5): height rod, tall clerk's desk, door, mirror, window onto a tree (seasons change in beats 4/6).
- Brain cutaway: real CC-BY brain parented to the hero's head bone; tumour/pituitary lumps; camera-attached teal→navy gradient card hides the set behind.
- X-ray: duplicate body with a fresnel glass shader, real spine model (bend deform = scoliosis), 110 glowing hormone particles routed along the limbs.
- Growth: armature scale 1.0 → 1.72 (4'6" → 7'8"), extra hand/foot/jaw/tongue bone scale (acromegaly).
- Theatre (x 3.65…10): iron bed, lamp, two surgeons + nurse; dive into the brain where forceps lift out the tumour.
- Exterior: cemetery behind the theatre; dusk HDRI fades in; young + old self side by side.

## Known issues
See the checkpoint notes in the director messages; updated at D.
