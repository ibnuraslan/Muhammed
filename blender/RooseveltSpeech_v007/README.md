# RooseveltSpeech_v007: farm package (hands pass on v004; v003 and v004 are kept unchanged)

25.0 s vertical short: 1080×1920, 60 fps, frames 1–1500. One continuous camera.

## Contents
- `RooseveltSpeech_v007_60fps.blend`:
  - 92.8 MB (decimal), packed and compressed. Textures are 1K (hero skin 2K) with a 2K HDRI, and the facade scans are decimated.
  - It is committed as a normal git file, with no LFS.
  - It opens and renders in factory Blender 5.2.2. See `package_check_factory_lowres.jpg`.
  - `package_for_farm` reports PROBLEMS: none.
- `SETTINGS.md` and `CREDITS.md` (with the CC-BY block for the video description).
- `../RooseveltSpeech_v001/beats.json`: beat start frames for the VO retime with `pipeline/retime_to_vo.py`.
- **No VO mp3 is included.** None was supplied.
- Review material in `../RooseveltSpeech_v001/review/`:
  - `v4_animlook_1s.jpg`: 1 still per second, v007 look.
  - `v3_0.2s_*.jpg`: stills every 0.2 s, from v003.
  - `audit_v3.json`.
- Rebuild:
  1. `01_build_humans.py`
  2. `02_build_scene.py`
  3. `03_animate.py`
  4. `04_shrink_textures.py`
  5. `05_decimate_bg.py`
  6. `pipeline/package_for_farm.py`

## Acting pass for v007 (client, Nov 12; `blender/briefs/ACTING_FIX_04-10.md`). The story-beat frames are unchanged
The full list, with frames, is in `../RooseveltSpeech_v001/review/ACTING_notes.md`.
- Before and after sheets: `review/ACTING_before_v006_0.5s.jpg` and `review/ACTING_after_v007_0.5s.jpg`.
- **Manuscript:** it no longer slides out of the pocket on its own. It rises only while his fingers pull it.
- **Policeman:** he no longer slides across the cobbles. His feet stay planted while he leans in and grabs the shooter.
- **Shooter:** his arm swings out and up instead of through his thigh. This was the clip_scan bad range at frame 79.
- **Camera:**
  - It is raised over the crowd heads at 1–2 s, and pulled back from the shooter's arm at the flash.
  - Beat 2 is now a full-body framing, so his feet and face are both readable.
  - In the x-ray, two framings where the paper filled the frame are pulled back.
- **Head:** he looks out at the crowd instead of up at the sky at 5.5–7 s.
- **Lift:** the lift of the paper arcs clear of the lapel.
- **Checks:**
  - `review/clip_scan_v007.json`: **0 bad ranges** (v006 had 1).
  - `review/qa_v007.json` (director `qa_check.py`): 3 INSIDE (camera inside the studio backdrop dome at the x-ray pull-out, intended). 0 EMPTY, FILL, HOVER, CLAW, FACEPRESS or BACKHEAD.
  - Hands: `pipeline/hand_poses.py` is used throughout (limits, poses, `grip_object` on the rail). The manuscript is pinched by thumb and index.
  - `review/hand_audit_v7.json`: 1 hit (4 mm at the lapel), 0 joint-range violations.
  - Hand close-ups: `review/v7_hand_closeups.jpg`.

## Moustache pass (from v006) (director, 23:26 UTC). Nothing else changed from v005
- The grey pad is replaced by a sculpted walrus moustache. Its centre line is ray-cast onto the rest-pose upper lip, so it follows the lip curve. It is tapered, droops over the mouth corners, and sits just off the skin.
- About 3,000 downward-combed particle strands (with children), using a Principled Hair BSDF in brown (melanin 0.55, redness 0.5) to match his hair. The base mesh is matte dark brown with a fibre bump.
- It is still attached to the head bone with Child Of, carried over from rest.
- **Close-up:** `../RooseveltSpeech_v001/review/v6_moustache_closeup_f300.jpg`.
- **Sheet:** `../RooseveltSpeech_v001/review/v6_moustache_1s.jpg` (1 still per second, 270×480, 8 samples).
- **Hand audit, re-run:** `../RooseveltSpeech_v001/review/hand_audit_v6.json`. 1 hit and 0 joint-range hits, the same as v005.

## Hands pass (from v005) (client, 23:00 UTC; see "Hands" in `blender/STYLE_ANIMATED.md`). Nothing else changed from v004
- **Limits:** Limit Rotation constraints in local space on every hero finger bone: fingers bend 0–90° forward with ±10° spread, and the thumb has a ±30° cone. The wrists are limited to ±60° flex and ±25° side.
- **Wrist targets:**
  - The hand direction is kept within 35° of the forearm and eased (at most 9° per key), so nothing snaps or bends the wrong way.
  - At the hit, the flailing hands follow the forearm.
  - The raised fist is curled less, so the fingers no longer fold into the sleeve cuff.
- **Pocket grab:**
  - The manuscript slides 6.5 cm up out of the breast pocket before the grab.
  - The hand arcs in from outside the coat, and the fist pinches the top edge from the side, with the thumb opposing the fingers.
  - The lift arcs away from the chest.
- **Crowd:** a relaxed default hand (fingers gently curled), and the clap motion stops short of the hands crossing.
- **Hand audit** (`../RooseveltSpeech_v001/review/hand_audit_v5.json`, every 2 frames, 750 frames, `scripts/07_hand_audit.py`). It checks the hero's fingers against his own torso, head and clothes, hand against hand, and joint ranges (finger back-bend and spread, wrist, elbow).
  - v004 had 81 penetration hits and 74 joint-range hits.
  - **v007 has 1 hit and 0 joint-range hits.** The one hit is a single finger point about 4 mm into the coat lapel at one sampled frame (around 1219–1227) while the fist lifts the paper past the lapel. It is not visible in the close-up.
  - Hand against other characters: the hero's hands never come within 1 m of anyone else.
- **Close-ups:** `../RooseveltSpeech_v001/review/v5_hand_closeups.jpg` (every hand action at 270×480).
- **Sheet:** `../RooseveltSpeech_v001/review/v5_hands_1s.jpg` (1 still per second).

## Look change (from v004) (client, 22:45 UTC; see `blender/STYLE_ANIMATED.md`)
Built from the v003 scene with `pipeline/anim_look.py`, then `RooseveltSpeech_v001/scripts/06_daylight_anim_look.py`:
- **Street:** bright daytime. A high sun clears the far-building shadow, the gas lamps, lanterns and headlamps are dimmed, and the lit windows are softened. The breath vapour is hidden, since it read as murky by day.
- **Cutaway:** the dome uses the sky-blue gradient (cyan at the top to near-white at the bottom), and the ghost rim is a deeper blue so it reads on the light backdrop.
- **Anatomy:** clean and colour-coded: cream bone, glossy pink-red muscle and lungs, with the wet coat reduced.
- **Wound:** a small clean dark-red mark only. The bullet is shown as an impact.
- **Hall:** brighter interior lights.
- **Grade:** AgX Punchy with exposure +0.45, motion blur off, f-stop at least 5.6, saturation ×1.25, bump ×0.35.
- **Sheet:** `../RooseveltSpeech_v001/review/v4_animlook_1s.jpg` (1 still per second, 270×480, 8 samples).

## Replaced since v002 (in v003, kept in v007) 
| Shot / time | v002 | v007 |
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
