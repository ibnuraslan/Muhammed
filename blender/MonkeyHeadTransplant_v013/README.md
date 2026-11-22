# MonkeyHeadTransplant_v013: farm package

This is the v012 film rebuilt to the batch-2 standard. It keeps the same VO, the same timing and the same frame range (**1–1656**, 60 fps, 1080×1920). v012 is untouched. No final render has been submitted.

- `MonkeyHeadTransplant_v013_60fps.blend` (78 MB): the self-contained scene, with all textures packed. It opens in factory Blender 5.2.2. `package_for_farm.py` reported PROBLEMS none.
- `MonkeyHeadTransplant_v013_VO.mp3`: the v012 voiceover, already on a sound strip in the .blend.
- `beats.json`: the synced start frame of each beat.
- `SETTINGS.md`: render settings and test frames.
- `CREDITS.md`: the CC-BY block for the video description.
- `review/preview.mp4`: the one full preview, rendered from this exact package. It covers every 5th frame at 270×480 with the VO.
- `review/pages/p01–p07.jpg`: the same preview frames as contact sheets. They were watched page by page.
- `review/*.json`: the four checks, run on this exact package.

**Source:** `../MonkeyHeadTransplant_v001/scripts`. Build order:
1. `01_build_monkey`
2. `01b_build_people`
3. `02_build_scene`
4. `03_animate`
5. `05_elbow_fit`
6. `pipeline/anim_look`
7. `04_anim_look_fixes`
8. `06_dress`
9. `pipeline/retime_to_vo` (with `anchors_v012.json`)
10. `pipeline/package_for_farm`

## Checks on the package (every 6th frame)
| Check | Result |
|---|---|
| `qa_v013.json` | FACEPRESS 0, INSIDE 0, ATTACH 0, HOVER 0, CAMJUMP 0.<br>CLAW 7: light curl on the surgeon's left hand during the head carry (synced 199–361) and the anaesthetist's bag hand (721).<br>ROLL 26: the approved x-ray camera move (961–1036).<br>PROPMOVE 66: the wall clock's hands ticking, which is intended.<br>EMPTY/FILL: the x-ray void and the macros. |
| `clip_scan_v013.json` | 0 frames with self or cloth intersections. v013a had up to 922 points at 451–517 and at the ending. |
| `limb_check_v013.json` | PROPHEAD 0. Before, the needle holder showed inside the surgeon's head.<br>ARMBODY: 2–3 points per arm on every character, under the gown. The body torso now stays under the gown instead of being cut away, so the check sees the armpit. Nothing is visible. |
| `body_prop_cross_v013.json` | These contacts are intended: the nurse's palms on the trolley tray while pushing it (1–150), and the anaesthetist seated on the stool. |

## Director's v013 items
1. **Faces.**
   - The MPFB faces have short hair under fitted caps.
   - The caps are ray-cast onto the hair and skinned to the head.
   - The irises are dark brown, with the eye shader fixed.
   - The new fitted white surgical masks run from the nose bridge to the chin, so the eyes and brows stay clear.
2. **Gowns.**
   - The gown top is fitted from the body and offset 4 cm, with smoothed cloth on the torso and folds.
   - It sits over the separate gathered skirt.
   - The gloves are separate (pale), and the caps are separate.
   - The scrub suit's upper half is removed under the gown, so no green shows through; only the trousers remain.
3. **Ending.**
   - The surgeon stays beside the chair at the monkey's left-rear from synced 1093.
   - At about 1447 he turns three-quarters to camera, lifts his head (face, mask, cap and eyes read) and raises his near hand in front of the monkey's face with a small wave, checking it.
   - The camera pushes in from the monkey's front-right. The monkey is fully in frame at about 41% of frame height, and the surgeon is 98% in frame with his head in.
   - The floor lamp was moved 0.6 m to make room.
4. **X-ray.** It is sharp (f/16) on a slow push in monkey space (synced 961–1093).
5. **Room.** The bare OR is dressed with:
   - an anaesthesia machine and gas cylinders
   - a supply shelf
   - an x-ray lightbox
   - a wall monitor
   - a crash cart and an oxygen cylinder
   - warm area keys, a cool rim light and a warmer floor

## Client flags A–E
A and B were checked by eye on the preview pages; C, D and E were fixed in code and also watched.

- **A.** The pen hand is clear of the other hand.
- **B.** The palm doesn't spin: it is wrist-limited, and the lamp is out of the transfer framing.
- **C.** The staples are ray-cast flush to the skin.
- **D.** The monkey is planted on the seat by ray-cast, with a bandaged seam and breathing.
- **E.** The end surgeon is re-staged as in item 3, with no chair clipping (the skirt clears the armrest).

## Known, not fixed
- **Stitching (synced ~401–596).** It is shot from the far side, so the surgeon faces the camera. His eyes are just above the frame top for much of it, and the dark sleeve openings read as black cuffs.
- **Head transfer (synced 251–316).** It is still a high three-quarter angle, and his cap dominates the top of frame.
- **Nurse at the monitor (synced 1251–1296).** The nurse at the monitor is cut at the right edge.
- **Pan to the monitor (~1101–1116, ~1240).** The surgeon leaves frame on the left as the camera pans to it.
- **Gown top.** The chest still reads faintly as a body shape at 270×480.
