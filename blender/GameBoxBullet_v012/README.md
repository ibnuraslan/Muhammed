# GameBoxBullet_v012: from-scratch rebuild (batch 1 film 15), ON HOLD, NOT READY

**Latest: check 4 (round 3, director-approved) FAILED.** See `review/CHECK4.md`. `review/preview.mp4` is now the round-3 preview. The .blend is still not pushed.


**Status: ON HOLD.** Self-QC check 3 failed (fresh harsh reviewer and my own watch). Both fix rounds allowed by the rebuild brief are used.
**No .blend is pushed**, because no check passed. `review/preview.mp4` is the check-3 preview: every 5th frame, 270x480, with the VO, rendered from the packed local build.
The remaining faults, with frames and the proposed fixes, are in `review/CHECK3.md`. Earlier rounds are in `review/CHECK1.md` and `review/CHECK2.md`.

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
