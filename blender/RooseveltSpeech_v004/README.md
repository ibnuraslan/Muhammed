# RooseveltSpeech_v004: farm package (animated look; v003 is kept unchanged)

25.0 s vertical short: 1080×1920, 60 fps, frames 1–1500. One continuous camera.

## Contents
- `RooseveltSpeech_v004_60fps.blend`:
  - 92.8 MB (decimal), packed and compressed. Textures are 1K (hero skin 2K) with a 2K HDRI, and the facade scans are decimated.
  - It is committed as a normal git file, with no LFS.
  - It opens and renders in factory Blender 5.2.2. See `package_check_factory_lowres.jpg`.
  - `package_for_farm` reports PROBLEMS: none.
- `SETTINGS.md` and `CREDITS.md` (with the CC-BY block for the video description).
- `../RooseveltSpeech_v001/beats.json`: beat start frames for the VO retime with `pipeline/retime_to_vo.py`.
- **No VO mp3 is included.** None was supplied.
- Review material in `../RooseveltSpeech_v001/review/`:
  - `v4_animlook_1s.jpg`: 1 still per second, v004 look.
  - `v3_0.2s_*.jpg`: stills every 0.2 s, from v003.
  - `audit_v3.json`.
- Rebuild:
  1. `01_build_humans.py`
  2. `02_build_scene.py`
  3. `03_animate.py`
  4. `04_shrink_textures.py`
  5. `05_decimate_bg.py`
  6. `pipeline/package_for_farm.py`

## Look change for v004 (client, 22:45 UTC; see `blender/STYLE_ANIMATED.md`)
Built from the v003 scene with `pipeline/anim_look.py`, then `RooseveltSpeech_v001/scripts/06_daylight_anim_look.py`:
- **Street:** bright daytime. A high sun clears the far-building shadow, the gas lamps, lanterns and headlamps are dimmed, and the lit windows are softened. The breath vapour is hidden, since it read as murky by day.
- **Cutaway:** the dome uses the sky-blue gradient (cyan at the top to near-white at the bottom), and the ghost rim is a deeper blue so it reads on the light backdrop.
- **Anatomy:** clean and colour-coded: cream bone, glossy pink-red muscle and lungs, with the wet coat reduced.
- **Wound:** a small clean dark-red mark only. The bullet is shown as an impact.
- **Hall:** brighter interior lights.
- **Grade:** AgX Punchy with exposure +0.45, motion blur off, f-stop at least 5.6, saturation ×1.25, bump ×0.35.
- **Sheet:** `../RooseveltSpeech_v001/review/v4_animlook_1s.jpg` (1 still per second, 270×480, 8 samples).

## Replaced since v002 (in v003, kept in v004) 
| Shot / time | v002 | v004 |
|---|---|---|
| Street, 0–7 s | Procedural brick box with blank white window panels; glowing cube lamp heads; canopy slab | CC-BY scanned brick facade (hotel) and side-building scans. Warm lit rooms with curtain drapes and mullions. Lantern-model heads on the gas lamps. A CC-BY 19th-century carriage at the kerb. |
| Street life | – | A policeman silhouette restrains the shooter after the shot, and breath vapour comes from the crowd and the hero. |
| Hero face | Black mesh moustache | Brown-grey particle-hair walrus moustache. Round wire spectacles. |
| Cutaway backdrop, 7.4–19.8 s | Pale cyan; pocket context lost | Deep navy-to-cyan gradient. The ghosted torso, coat, ribs and lungs stay visible around the pocket the whole time. |
| Manuscript | Flat stack of cards with a tube for a spine | 50 real U-folded pages with staggered torn edges, fibre texture, yellowing and illegible handwriting strokes. The pages fan open on the reveal and riffle under the bullet, then the bullet punches a torn hole and paper flecks spray out. |
| Glasses case | Glass-looking rounded box | Brushed, worn steel clamshell with old dings, a seam, hinge knuckles and a pin, plus the bullet dent. |
| Ribs / lungs / muscle | Clean white ribs, smooth red disc | Porous bone shader on the CC-BY ribcage. Wet SSS lungs. A fibrous, displaced chest-muscle layer holds the bullet. |
| Bullet | Primitive streak cone | Removed; the farm's motion blur carries the streak. Lead slug with surface irregularity. |
| Hall, 19.8–25 s | No stage lighting | Brass footlight hoods with bulbs along the stage lip, and two follow-spots from the balcony. |

## Audit (`audit_v3.json`, every 5th frame)
| Check | Count |
|---|---|
| Feet hover, sink or slide | 0 |
| Camera inside geometry, outside the x-ray dome | 0 |
| Head items overlapping the face | 0 |
| BVH penetration (left fingers into the brass rail while gripping, under 4 mm) | 2 |

## Known issues
- The paper fills about 75 % of the frame around 14.2 s for about 0.3 s. It shows handwriting and fibre detail, not a blank colour.
- The hero's moustache reads as a solid mass at very low angles.
- Teeth show faintly through the ghosted head at about 19 s.
- The hall crowd is not audited for hand-to-hand contact.
- The policeman was moved after the v3 sheets were rendered: he now stands on the shooter's right, out of the camera's path.
