# CaveRescue_v012: final restage round (batch 1, film 23)

**Status: ON HOLD for the director's review.** The package passes the render check below. I have watched every
page of `review/preview.mp4`, which was rendered from this exact file (md5 `75b47982993fe214ff18452c4468b5dd`,
270×480, every 5th frame, with the VO). A few short transition spans are still weak; they are listed under "Open items".

One continuous camera, built to the client's VO (beats 1/341/571/687/891/1065/1160/1321/1463/1591/1761/1885/2105/2249),
frames **1–2436** at 60 fps. The source version `CaveRescue_v011` is untouched.
Rebuild: `scripts/00_assets.py` → `01_build.py` → `02_animate.py` → `03_package.py`. `04_checks.py` holds the film checks.

## What changed from v011 (the client's fix list)
- **Underwater beats.** The volumetric water is gone: no murk, and far cheaper to render. It is replaced by
  `lib_fog.py`, a teal emission-gradient fog spliced into every material. It switches on only on frames where the
  camera is under water, and it runs bright teal near the surface and deep blue-teal at depth.
  The divers are lit by:
  - a helmet lamp (spot light plus an emissive lens)
  - a warm face light
  - a cyan rim light on the back, shoulders and helmet
  - a soft fill light riding on the camera
- **Dive transitions.** The camera follows Diver 1 down into the sump and holds 2–3 m behind him. He hovers in the
  foreground while the lone diver's lamp goes on and dims (it never goes fully dark), then he swims back up and surfaces
  with the camera. The tow starts in the chamber pool, so the stretcher and the towing diver lead the dive.
  Swimmers now swim head first; v011 had them swimming feet first.
- **Lens.** In `04_checks.py` the stretcher never comes closer than 1.15 m to the lens, and the ambulance stays more
  than 8 m away.
- **Cutaway.** The cut face is now real rock texture (Poly Haven Cliff Side at two scales) under saturated strata
  bands, with dark fracture lines and a strong bump. The front opens and closes instantly while the camera sees only
  back-half rock. In `04_checks.py`, at most 0.5 % of a frame shows front-half rock at any open or close frame, so no
  mountain rises into view. The second cutaway closes while the camera is inside the passage near the mouth, and then
  the carriers walk out into daylight.
- **Limbs.**
  - Elbows and knees are true hinges, with no twist, no sideways bend and no bending past straight. Their limits are
    set from each rig's rest bend, up to a maximum of 148° at the elbow and 150° at the knee.
  - Finger and wrist limits come from `hand_poses`.
  - The wetsuits have textured elbow and knee pads, coloured cuffs and thigh panels, and a ribbed neoprene bump, so
    limbs read as jointed limbs, not tubes.
- **Ambulance.** A real CC-BY model ("Shvan '92 Ambulance", credited in CREDITS.md) with every readable text removed.
  It carries a DA KRAS FILMS logo plate on the side.
- **Render time.** The fog is never sampled as a light, and the file renders at 12 samples with OpenImageDenoise and
  fewer bounces. The measured times are below.

## Render check: PASS
Run on the exact file `CaveRescue_v012_60fps.blend` (90.4 MB, md5 `75b47982…`) with
`blender --factory-startup -b` (Blender 5.2.2, no add-ons):
- It opens with no errors, no missing files, 0 linked libraries, every image packed and the VO sound packed as strip
  `VO`.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–2436, output `//render/CaveRescue_v012_####` (PNG).
- Cycles at 12 samples, adaptive threshold 0.08, OpenImageDenoise.
- Full-resolution test frames, measured on a 4-core CPU container with no GPU. All are under the 120 s limit, and
  none is black, empty or pink:

| Frame | Shot | Render time |
|---|---|---|
| 1 | the walk-in | 59.9 s |
| 1200 | the sump | 107.5 s |
| 1950 | the tow | 98.8 s |
| 2436 | the end shot | 68.4 s |

- `04_checks.py` results (in `review/checks_v012.json`):
  - TELEPORT 0, JUMP 0, INSIDE 0.
  - FRONTPOP: at most 0.5 % of a frame at every cutaway open and close frame.
  - LENS: the stretcher comes to 1.15 m at f1999–2003. This is a diver-side close-up and the stretcher isn't blocking
    the lens.

## Open items (from watching the preview; frame numbers are film frames)
- **f546–566 (0.35 s):** plain cave wall after the boys run past, just before the cross-section opens.
- **f991:** one darker frame in the chamber as the diver's lamp swings onto the boys.
- **f1111–1121 (about 0.2 s):** under water, a bright rectangle (light through the pool surface seen from below),
  then the ledge floor fills the frame as the camera follows Diver 1 down.
- **f1341–1366 (about 0.4 s):** Diver 1 surfaces and the camera turns across the open pool to the rescuers, mostly
  water and cave wall. `04_checks` SUBJECT flags f1346–1354.
- **f1881–1911 (about 0.5 s):** a wide view of the pool with the tow small on the surface, before the camera dives
  close (SUBJECT f1878–1884).

## Logo
DA KRAS FILMS appears on the rescuers' gear bag in the chamber (f1470–1600) and on the ambulance side
(readable f2150–2436, large f2350–2436).
