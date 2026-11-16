# BogBurials v002b (ConnectB33)

Vertical explainer, 1080×1920, 60 fps, built to the client VO (Windover bog burials, Florida).

- `BogBurials_v002b_60fps.blend`: farm package (frames 1–2187)
- `BogBurials_v002b_VO.mp3`: client VO
- `beats.json`: shot start frames from the VO word times (`1 + round(s × 60)`)
- `review/preview.mp4`: every 5th frame, 270×480, Cycles 4 samples + OIDN, with the VO, rendered from this exact package
- `review/`: contact pages, check results (clip_scan, qa_check, limb_check, body_prop_cross)
- `scripts/`: `01_lib.py` (asset library), `02_build.py` (+ `shots.py`, `curl_pose.py`, `skel_bind.py`), `03_package.py`

Rebuild: `01_lib.py` on the rigged wolf (`pipeline/rig_quadruped.py`) → `02_build.py` → `03_package.py`.

Shots (VO): 01 placed in the water · 02–03 knees to chests (underwater) · 04 the driven stakes around her (underwater) · 05 stakes around the body ·
07 kept from floating up · 10 dead plants settle, peat rises · 11 the lid (cross-section) · 12 blocking out air ·
13 slowing decomposition (underwater close) · 14 8,000 years later (site) · 15 construction workers (logo on the pickup door) ·
16 a human skull · 17 archaeologists · 18 168 burials · 19 preserved so well · 20 stomach contents · 21 brain tissue ·
22–23 burial cloth around the bones.
Logo: one placement, the white pickup's driver door (S15). No other text.

## Staging decisions in v002
- S04 "then drove wooden stakes": the stakes stand driven around her and the camera tracks along them underwater, with both
  men standing behind in the water. Five versions with a hand pushing a moving stake all clipped the hand or arm (body_prop_cross),
  so per LESSONS §2.15 there is no hand–stake contact. The VO carries "drove".
- S19 "preserved so well": the archaeologist sweeps loose soil with her flat hand beside the bones. A brush could not be held
  without the fingers clipping it, and it was invisible at this framing.
- The VO has no animal line and no closing "curled shape" line, so the P1 wolf shots and the final "as she was buried" shot are not used.

## v002b (director notes on v002)
1. Burial party: real clothes. Belted wool tunics (brown / oatmeal) whose skirt reaches mid-thigh, trousers in a darker
   colour, and wool shoulder cloaks (`scripts/05_clothes.py`).
2. The deceased: a draped wool burial cloak, cloth-simulated once onto her fixed curled pose, plus wool leg wraps. Face and
   hands show; no bare legs. S13's underwater close-up now frames her face in the cloth.
3. S10: the peat stops at her top and the camera stays well under the surface (no soil in the lens).
4. S12: the air bubbles stay inside a visible water layer above the peat lid.
5. Pickup: the logo sits on a flat white door sign and reads in full, "DA KRAS FILMS". The cab glass is clean dark glass, and the
   licence plates and tailgate lettering are painted plain.
6. S16: the skull's eye sockets and teeth face the camera.
Re-rendered preview ranges: f1–941 and f1101–1281, spliced into the v002 preview.
