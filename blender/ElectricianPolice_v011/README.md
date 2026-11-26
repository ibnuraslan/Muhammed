# ElectricianPolice_v011: from-scratch rebuild, client-approved, ready to render

**Status: READY TO RENDER.**
- The client approved this build as it is (relayed by the director on 26 Nov).
- `review/preview.mp4` is the moving preview of this exact build: 270x480, every 5th frame, with the VO, 24.1 s.
- Watch it before paying for the render.

## Render check: PASS
Checked on the exact delivered file, `ElectricianPolice_v011_60fps.blend` (39 MB, md5 `d912bb0c658c691cac3fc06fbc7af457`).
- **Opens cleanly:**
  - It loads with `blender --factory-startup -b` (Blender 5.2.2) with no errors and no missing files.
  - There are no linked libraries, no unpacked images and no unpacked sounds.
  - It needs no scripts, drivers or add-ons.
- **Scene settings:**
  - Camera: `CAM_Film` is the only camera, and there are no camera markers.
  - Resolution and frames: 1080x1920 at 100 %, 60 fps, frames 1-1446.
  - Output: PNG to `//render/ElectricianPolice_v011_`.
  - Audio: the VO strip is packed, at frames 1-1419.
- **Test frames:**
  - Frames 1, 723 and 1446 were rendered at full 1080x1920 from the packed file. None is black, empty or pink.
  - The check used 16 samples to save time; the farm setting is 64 adaptive.
  - CPU time was 76-111 s per frame on 4 cores at 16 samples.
  - Downscaled copies are in `review/render_check_*.jpg`.

## What it is
- **Timing:** built to the client's VO from v010 (`ElectricianPolice_v011_VO.mp3`) from the start. The beat frames are in `beats.json`.
  - The recording's wording differs from the brief's script ("He got fined by the police...", "Big mistake...", "dug through the records..."). The picture follows the recording.
- **Camera:** ONE continuous camera with no cuts. Scenes change inside the move:
  1. A street chase to the bike stop at the police station.
  2. A whip along the wires to the substation, and a crane up the pylons.
  3. Down through the control-room window.
  4. Out of that window and across the street.
  5. In through the station window.
  6. Back out to the dusk street.
- **People:** two MPFB people, one model each: Ravi (the electrician) and the traffic officer.
  - They wear real loose MakeHuman community CC0 garments (polo shirts and wool trousers) with solidify thickness.
  - The skin is masked only under the cloth, and no crotch holes were found in close renders.
  - Ravi's hard hat and the officer's peaked cap are rigid, fitted to the scalp, and are Child Of the head bone.
  - Eyes use the EnhancedEye cornea fix.
- **Contacts:**
  - The rider's hands use solved wrap grips on the handlebars.
  - The lever was re-staged within reach, with a wrap grip on its red handle.
  - The officer's hands rest flat on the desk with bent elbows.
  - A near-lens check (rays from the camera every 2nd frame, nothing within 30 cm) finds 0 frames.
- **Logo:** DA KRAS FILMS is on the back of the laptop lid. It is sharp and uncropped from about frame 576 to 686 (about 1.9 s, with his face above it). It also appears on a framed print on the control-room wall.
- **Build:** `scripts/01_people.py`, then `scripts/02_set.py`, then `scripts/03_animate.py`, then `pipeline/package_for_farm.py`. `scripts/lib.py` holds the shared helpers.
  - The garments are the MakeHuman community packs `shirts01`, `pants01` and `hats01` (CC0), unpacked into MPFB's clothes library.
  - The set reuses CC-BY/CC0 props from the v010 asset library; see `CREDITS.md`.

## Known (the last harsh review, check 5)
The client approved the build with these known. The full list is in `review/CHECK5.md`.
- **The cut, 1041-1081:** it reads as an arc flash plus a red emergency tint more than a full blackout.
- **Brief faceless or back-view stretches:** 51-111, 301-331, 456-496 and 906-956.
- **Near-static hold, 711-856:** at the console.
- **Arms hang fairly straight:** 381-401 and 1291-1376.
