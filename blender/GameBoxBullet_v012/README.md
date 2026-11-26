# GameBoxBullet_v012: from-scratch rebuild (batch 1 film 15), CLIENT-APPROVED, READY TO RENDER

**Status:** the client approved the round-4 build as it is (relayed by the director on Nov 26).
- This package is exactly that build: `GameBoxBullet_v012_60fps.blend`, frames 1–1311 at 60 fps, with the VO packed.
- `review/preview.mp4` is the preview of this exact file: every 5th frame, 270x480, with the VO, 21.9 s. Watch it before paying for the render.
- `SETTINGS.md` is the farm sheet. `CREDITS.md` lists the assets; all are CC0.

## Render check: PASS
Checked on the exact delivered file, `GameBoxBullet_v012_60fps.blend` (64 MB):
- **Opens cleanly:** it loads with `blender --factory-startup -b` with no errors. There are no linked libraries, no unpacked images, sounds or fonts, and no drivers or scripts.
- **Scene settings:**
  - Scene camera `CAM_Film` (the only camera, no markers).
  - 1080x1920 at 100 %, 60 fps, frames 1-1311.
  - Cycles: 64 samples, adaptive (threshold 0.04), OpenImageDenoise.
  - Filmic, High Contrast.
  - PNG output to `//render/GameBoxBullet_v012_####.png`.
  - The VO strip is present (frames 1-1285).
- **Test frames:** frames 1, 656 and 1311 were rendered at full 1080x1920 from the packed file. None is black, empty or pink.
  - The check used 16 samples to save time; the farm setting is 64 adaptive.
  - CPU time was 35-80 s per frame on 4 cores at 16 samples.
  - Downscaled copies are in `review/render_check_*.jpg`.

## Known items from the last harsh review (client approved the build with these)
See `review/CHECK5.md` for the frames:
- the bullet is small in the front-angle box macros;
- fingertips show at the box edge at the hit;
- a cabinet sits near the lens in the room approach;
- some near-static mediums;
- face crops on several push-ins;
- the shooter's bright eyes.

## What v012 is
- **Timing:** the client's VO, the same file as v010/v011 (`GameBoxBullet_v012_VO.mp3`). Frames 1-1311 at 60 fps, built to the word timestamps from the start, with no retime. Beats are in `beats.json`.
- **One continuous camera, no cuts:**
  - the shooter on the sidewalk, with the muzzle flash at f10;
  - riding beside the bullet over the lawn;
  - the bullet punches the siding (f99), and the camera slides in through the open window;
  - the slow-motion bullet flies toward him;
  - his face and the box with the logo;
  - his right profile at the hit (f519);
  - the crack spreads on the box front;
  - over the open top, the content layers burst as the bullet ploughs through (layer breaks at f637, 689, 774 and 809);
  - the bullet stops at half depth with the back layers intact;
  - he lowers the box onto his lap, looks up, and takes a long eyes-closed exhale, with the logo poster behind him.
- **People:** one MPFB model each, in real MakeHuman community CC0 garments, recoloured.
  - Him: a crude t-shirt and cargo pants.
  - The shooter: a fisherman sweater and wool pants.

  The skin is masked only right under the cloth. Garments are solidified and opaque, and leg and crotch skin take the trouser colour, so there are no holes or skin reads.
- **Staging:**
  - He sits ON the sofa: the pelvis is on the measured seat top and the feet are on the floor.
  - Palms rest on the box sides and the fingers wrap the front edge.
  - The bullet and the box are one object each for the whole film.
- **Logo:** on the box art, and on a framed poster on the back wall.

## Build
1. `scripts/01_build.py <assets> <logo_white> <logo_dark> base.blend`. This is the set, people and props. The assets are Poly Haven sofa_02, potted_plant_01 and shrub_01 (1k). The garments come from the MakeHuman community packs shirts01 and pants01.
2. `scripts/02_animate.py out.blend`. This is the staging, acting, bullet, box, wall break, camera and VO.
3. `scripts/03_slim.py`. This removes duplicate images and shrinks background textures.
4. `pipeline/package_for_farm.py`. The result is 64 MB packed. The farm checks report no problems.

## Checks on the round-2 build
- `clip_scan`: 0 bad ranges.
- `limb_check`: ARMBODY 2-point hits only (the upper arm at the shoulder, the known false positive).
- `body_prop_cross`: flags hand edges at the box sides. Close renders at f301, f601 and f1250 show the palm about 4 mm off the side, with no penetration.
