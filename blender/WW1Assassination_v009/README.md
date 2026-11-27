# WW1Assassination_v009: from-scratch rebuild after 3 fix rounds (round 3 approved by the director)

**Status: Render check PASS. ON HOLD until the director has watched `review/preview.mp4`.**
`review/preview.mp4` is the full preview of this exact build: every 5th frame, 270×480, with the VO. Watch it before rendering.

Package: `WW1Assassination_v009_60fps.blend` (97 MB, everything packed). Built to the client's VO (`beats.json`), frames 1–1826 at 60 fps, one continuous camera.
Attribution is in `CREDITS.md` (CC-BY: the car and the pistol; the rest CC0 or public domain). v008 is left untouched.

## Build (scripts/)
`fetch_assets.sh` → `01_build.py` → `02_animate.py` → `03a_map_raster.py` + `03_map.py` → `04_slim.py` → `05_farm_settings.py` → `pipeline/package_for_farm.py`.

## The film
1. The gunman fires at the open car outside the DA KRAS FILMS cafe (the logo is readable f1–40 and again about f1100–1240).
2. The rewind takes us to the quay.
3. Two would-be assassins lose their nerve.
4. A third throws the bomb, which bounces off the folded hood and blows up under the second car.
5. The overhead follows the car to the wrong turn and the stall.
6. Side-on, the gunman fires twice, and the Archduke and the Duchess slump.
7. The camera rises over the car while the whole city shrinks onto Sarajevo on a 3D map of 1914 Europe.
8. The war spreads from Austria-Hungary and Serbia across the alliances (red / blue, with an orange fire front).

## What v009 fixed (from watching every page plus the checks)
- **The rise to the map:** the cloud white-out is replaced by the city shrinking onto the map (one move, no empty frame). The map is a real grid mesh, with deep colours and a sharp raster.
- **Camera:**
  - No lens blockers: it stays off the suit, the fender and the lamps.
  - It flies over the bunting, and the cross bunting is removed under the overheads.
  - The whip at f41–50 is clean, and the join at f1432 is seamless.
  - The shots are staged side-on, with the gunman fully in frame until his arm is down (f1252–1370).
- **Bodies:**
  - Seated lap hands are out of the thighs, and the crowd's hands are off their hips (clip_scan clean).
  - Natural, relaxed arms.
- **IK feet on the real floors:** the car floor 0.0–0.1 cm, the pavements ±0.4 cm (were 0.9–1.7 cm under).
- **The pistol** sits in a closed fist at every frame (checked at 1080p). The bomb is in the palm until the throw.

## Checks on the final build
- **clip_scan:** clean (no bad ranges).
- **qa_check:** CAMJUMP, FILL, INSIDE, ROLL, CLAW, FAN and PROPMOVE all 0. The other flags:
  - EMPTY: f43 (whip), f739–763 (the bomb macro, intended), and the map from f1501 (no people by design).
  - BACKHEAD: f913, 1057 and 1435 (overheads of the car).
  - HOVER and FACEPRESS: only inside the shrinking city (from f1495, below one pixel).
  - ATTACH: the helmet sits on the hair, 4–5 cm off the skin.
- **limb_check:** 2-point upper-arm/shoulder hits on seated and relaxed MPFB rigs (shoulder volume, not visible). Q3's background wave at f637–697.
- **body_prop_cross:** the Pistol hits are the fist grip. The Car1/Car2 hits are the seated bodies inside the car-body mesh volume (seats and floor are part of it). None of them is visible.
- **Remaining minor note:** f821–846, the quay bunting pennants cross the lower third of the frame as foreground after the blast.

## Render check: PASS
On the exact file `WW1Assassination_v009_60fps.blend` (97 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed. No drivers and no Python.
- No errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1826, PNG to `//render/WW1Assassination_v009_####.png`, and the VO strip at frame 1.
- Cycles: 28 adaptive samples (threshold 0.06) plus OIDN, AgX Punchy.
- Full-resolution test frames on a 4-core CPU with no GPU:
  - f20 in 114 s (the heaviest frame, measured on this exact file)
  - f800 in 87 s, f1300 in 81 s, f1700 in 63 s (same settings, before the final re-pack)

  All are 120 s or less. None is black, empty or pink. Side by side with 64 samples there is no visible difference.
