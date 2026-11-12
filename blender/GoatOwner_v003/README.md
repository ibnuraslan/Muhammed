# GoatOwner v003 (director fix on top of v002)

The only change from v002: the goat's mouth interior was saturated red and read as blood near the attack (11–17 s). Strong reds on the goat material (M_Goat) are now pulled to a dark neutral brown, so the goat's fur colour is unchanged. Animation, camera, look and hands are identical to v002. See `package_check_f721_lowres.png`.

Still open from v002 (minor): a brief camera brush past his back at about 20 s, an official's arm close to the lens at 31 s, and some twist in the goat's body at 11–13 s.

---
# GoatOwner_v003: farm package (Connect32)

This is the full 36.5 s film at 1080×1920 and 60 fps (frames 1–2190), ready for RenderStreet. No render has been submitted.

- `GoatOwner_v003_60fps.blend` (**69 MB**, compressed, normal git file, no LFS) is the self-contained scene. All textures are packed. One camera, `CAM_Film`, makes a single continuous move.
- `SETTINGS.md` is the farm render sheet and lists test frames. `CREDITS.md` has the CC-BY block for the video description.
- `beats.json` gives the beat start frames and first words. When the VO arrives, retime with `pipeline/retime_to_vo.py`, then lay the mp3 at frame 1.
- `package_check_f960_lowres.png` is a 25 %, 4-sample frame rendered from the packed file in factory-startup Blender. It proves the package opens and renders; it is not a quality reference.
- `hand_audit_D.txt` is the hand audit of this build: a BVH overlap check every 4 frames covering hand vs hand, hand vs own body/clothes, and hand vs other characters and the goat.
- Review sheets, close-ups and the contact audit are in `../GoatOwner_v001/review/`.

The source is `../GoatOwner_v001/scripts/`, and `05_package.sh` rebuilds everything. The order is:
1. the goat rig, then `01_build_humans.py`, `02_build_scene.py` and `03_animate.py`
2. `pipeline/anim_look.py --no-sky --exposure 0.15`
3. `04_shrink.py` (≤1K textures), then `pipeline/package_for_farm.py`

## Look
- The studio look pass per `STYLE_ANIMATED.md`: AgX Punchy, saturation up, bump softened, roughness at least 0.35, f-stop at least 5.6, motion blur off.
- We keep our own clear blue HDRI sky with soft clouds, so `--no-sky` is used.

## Known issues
- **Hand audit:** 4 flagged samples remain. All are brief transitions where an official's hand brushes his or her own jacket hem or cuff:
  - 28.4 s (OffA right, OffB left)
  - 31.1 s (OffA right)
  - 5.9 s: the passer-by in the far background, at 7 polygon pairs

  There are no hand-to-hand or hand-through-another-character overlaps.
- **Joint limits:**
  - Wrists carry Limit Rotation (±60° flex, ±25° side, ±40° twist).
  - Finger and thumb Limit Rotation was tried and removed: its local-Euler clamp flattened the keyed MPFB finger curls into open, splayed hands.
  - Fingers are only ever keyed forward (0–75° about the knuckle axis), so none bends backward.
- The official holds the catch pole one-handed; with two hands, they collided with each other.
- The rescuer's feeding hand sits just above the grazing goat's head rather than under its muzzle in some frames.
- Hooves float 3–4 cm mid-trot during the charge and sink 3.5 cm on one porch step (27.7 s).
- The goat's mouth interior (red) shows at some angles in the head close-ups at 11–12 s. The camera was pulled back to minimise it.
- The stick grip in beat 1 reads as the stick resting across the top of his raised hand, with the thumb out, rather than a full fist wrap. See `D_contact_closeups.jpg` at 0100.
- No voiceover yet, so timing follows the brief's target beat times.
