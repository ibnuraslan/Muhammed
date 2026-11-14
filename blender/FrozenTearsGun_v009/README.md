# FrozenTearsGun_v009: farm package

This is v008 plus the director's v008 review notes (Nov 14). Beat frames are unchanged and no VO was added. It is the full 35.0 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `FrozenTearsGun_v009_60fps.blend` (69 MB, compressed, normal git file, no LFS): the self-contained scene. Every texture is packed. It opens and renders in factory-startup Blender 5.2.2.
- `SETTINGS.md`: render settings and test frames.
- `CREDITS.md`: all assets are CC0, so no attribution is required.

## Source and rebuild
The source is `../FrozenTearsGun_v001/`: `PLAN.md`, `beats.json` and `scripts/`.

To rebuild, run `scripts/build_all.sh` from that folder. It runs:
1. `01_build_humans.py`: MPFB2
2. `02_build_scene.py`: sets, the procedural gun and props, lights, render settings
3. `03_animate.py`: all animation and the camera

Then run `scripts/shrink_for_farm.py` after `pipeline/anim_look.py`, `scripts/05_anim_look_fix.py` and `scripts/06_hands_pass.py` (chain: `scripts/build_v006.sh`) (textures to 1K, 2K for her face skin, a 1K HDRI, opaque maps re-encoded to JPEG, orphans purged), and package with `pipeline/package_for_farm.py`. The review tools are `scripts/stills_at.py`, `scripts/audit.py` and `scripts/camera_path_dump.py` / `camera_path_plot.py`.

## Voiceover
No VO was supplied. The film is built to the target beat times in `beats.json` (13 beats; frame = 1 + round(t × 60)). When the VO arrives:
1. Get word times with `pipeline/transcribe.py`.
2. Write the anchors (old frame from `beats.json` → second of each beat's first word).
3. Run `pipeline/retime_to_vo.py`. It warps every keyframe, including the camera and the exposure flashes, and lays the VO strip at frame 1.

## v009b (director's v009 review)
- **Tear-wipe.** Her fingertips touch her cheek under the eye for about 0.4 s (24.0–24.4 s), then her hand drops to her lap. Her face stays visible.
- **Swing into the photo.** It is now a quick whip straight from her to the photo; no lamp, toolbox or door frames.
- Nothing else changed. `review/clip_scan_v009.json` has no bad ranges.

## Changes in v009 (director's v008 review)
- **The workshop stays behind her.** The blue explainer backdrop card (4.2–15.9 s) is switched off, so the brick and pegboard workshop is behind her in every shot.
- **Her arms read as attached.** The workshop medium shots are pulled back about 30 % so her elbows and forearms are in frame.
- **Mentor's flinch.** His hands stay relaxed at his sides (no crossed arms, no claw hands).
- **Time-lapse sketch pose.** Her hands are on their own sides of the paper (no crossed forearms).
- **Fewer empty frames.**
  - She stays face-on while the tears fly off.
  - The swing into the photo is quicker.
  - The camera holds on the mentor until the flash that takes us back to the workshop (no blank wall).
- **Ending.** It uses a longer lens from further right, so his head is only a soft edge and her face is larger.
- QA on the final build: `review/qa_v009.json` has 40 flags (v008: 46).
  - Eleven are "no character in view". The longest such stretch is the 0.5 s push into the photo.
  - The CLAW flags are her firing fist on the grip and the vice grip.
  - The FACEPRESS flag is the brief fingertip tear-touch.
- `review/clip_scan_v009.json` has no bad ranges.

## Changes in v008 (director's v007 review)
The moving preview is `../FrozenTearsGun_v001/review/preview.mp4` (every 5th frame, all 420 frames; contact pages in `review/preview_pages/`). Every page was watched.
- **Framing.** The workshop is now mostly medium shots of her face with the gun in her hands. Gun close shots are kept to about 3 s in total: the tears dropping into the chamber (4.4–5.3 s), her hand on the valve (6.1–6.7 s) and the shot itself (about 15 s). The opening eye close-up widens at about 1.5 s.
- **Pellet flight.** She stays in frame watching the frozen tears fly off. The camera swings to the photo only for the last half second, so there is no empty room.
- **Her crying (office).** Her hand no longer presses over her face. At about 24 s she touches a tear from beside her eye with her fingertips, briefly, with her face visible. The other hand stays on her lap.
- **Thought bubble removed,** along with the floating drops in the office.
- **Mentor.**
  - In the office his arms are relaxed and bent, and his jab bends at the elbow.
  - At 26.2–27.6 s he flinches a little, with his hands up in front of his chest; no palm touches his face.
  - In the finale he braces with his elbows bent and his hands in front of his body; no T-pose.
- **Office camera.** The whip pans now orbit around her side. The office desk lamp and window blinds (read as a floating lamp and diagonal stripes) are removed.
- **QA on the final build.** `review/qa_v008.json`: 46 flags (v007 112).
  - The longest stretch with no character in frame is the 0.5 s push into the photo, with the tears flying (18.3–18.8 s).
  - The CLAW flags are her firing fist on the gun grip and the time-lapse vice grip.
  - The one FACEPRESS flag is the brief fingertip tear-touch (frame 1447).
  - `review/clip_scan_v008.json` has no bad ranges.
- **Ending.** It ends on her face, holding the gun, over the mentor's shoulder.

## Changes in v007 (moving-preview fixes)
The moving preview is `../FrozenTearsGun_v001/review/preview.mp4` (contact pages: `review/preview_pages/`) (`pipeline/preview.py`, every 5th frame, 12 fps, frame numbers burned in). Faults found in the v006 preview and fixed in `scripts/03_animate.py` (camera waypoints only; animation and beats untouched):
- 2.1–4.4 s: the tear-tube ride was a 70 mm f/5.6–8 macro (blurred cheek and a giant funnel filling the lens for about 1.5 s). It is now a 45 mm f/11 mid shot that follows the tear about 30 cm back.
- 4.4–5.5 s: the chamber-lid macros (giant blurred lid) are now 50 mm f/16 mid shots, about 35 cm off.
- 7.5–7.9 s: the camera path ran through her valve hand (giant blurred hand). The 7.8 s waypoint now swings round outside the hand.
- 8.3–12.2 s: the in-chamber macros (70 mm f/32–40, blurred pellets and a giant finger behind the glass) are now 50 mm f/16 mid shots of the gun in her hands.
- 13.0–14.8 s: the barrel and finger macros (gold barrel and fingers filling the frame) are now 42–45 mm f/16 mid shots, about 40 cm off.
- 16.3–18.85 s: the pellet ride sits further back and to the side (no pellet crosses the lens) at f/11. The blank, pale frame at 18.7 s is gone.
- 32.1 s finale: the camera no longer passes 20 cm behind her head. It is a side view of her aiming and firing the gun in her hands.
- QA rerun on the final build: `review/qa_v007.json` (148 flags in v006, 112 now; the rest are the kept flags explained in `ACTING_notes.md`), and `review/clip_scan_v007.json` has no bad ranges.
- The wrist limit in `scripts/06_hands_pass.py` now uses YXZ order (LESSONS_LEARNED section 2).

## Changes in v006 (acting pass)
The full list, with frames, is in `../FrozenTearsGun_v001/review/ACTING_notes.md`.
- **Office.**
  - Her hands now rest on her thighs. This was a bug: the old targets pointed back to the workshop, so her arms went behind the chair and through the armrest.
  - She looks up at him and flinches when he slaps the desk.
  - While crying she shakes her head and wipes her eye.
  - Beat 11 now opens on her face.
- **Time-lapse.**
  - Her feet stay planted and the vice is closer, so she only shifts her weight.
  - Pose changes are quick blends, not snaps.
  - The pencil is held between her thumb and index, and the file lies across both palms.
- **Hands on the device.**
  - The valve pinch is real.
  - The support hand wraps the canister without touching the grip hand or the spring glass.
  - The aim position is a little closer so her arm isn't at full stretch.
- **Camera.**
  - The fog-filled (9.5 s) and blown-white (11.3 s) chamber frames are reframed.
  - The camera stays further back from the photo before the flash.
  - A new in-between at 21.9 s replaces an empty-wall whip.
  - The camera no longer brushes her at 31.5 s, and the 28 s mentor framing is wider.
- **Cleanup.**
  - Rig-widget meshes from the rigged Poly Haven props (including a "KEY" text widget) no longer render.
  - The lettering in her jeans' normal map and on the tool-chest badge is removed.
- **Round 2 (director review):** real hand shapes for every contact.
  - writing grip on the pencil
  - one hand wraps the file, the other is flat on it
  - she grips the gun on the bench and carries that grip as it lifts
  - flat-palm desk slap
  - hooked valve grip with no splayed thumb
  - palm over the eyes, then a knuckle wipe
  - the pellet flight keeps the photo in frame and in focus
- **Checks:**
  - director `clip_scan.py`: 0 bad ranges
  - hand audit: 13 samples, all contact while touching her own face or mid-blend, explained in the notes
  - contact audit: no problems
- **Sheets:** `review/acting_before_v005_0.5s.jpg` and `review/acting_after_v006_0.5s.jpg`. Close-ups: `review/hand_closeups_v006.jpg`.

## Changes in v005 (hands only)
- **Joint limits** (`FrozenTearsGun_v001/scripts/06_hands_pass.py`):
  - Limit Rotation constraints, in local space, on every finger: 6–90° forward bend (a relaxed curl floor), no backward bend, small spread.
  - The same on every thumb (a natural cone) and both wrists: flex ±70°, side ±30°, twist ±90° as a pronation proxy, because forearm twist is locked in the IK.
  - The IK elbow is a pure hinge, 0–145°, with no hyper-extension. It previously reached −40°.
- **Real grips:**
  - The right hand wraps the gun grip: palm on the grip's side, fingers around its front, thumb opposing, index on the trigger.
  - The left hand cradles the CO2 canister from below.
  - The valve hand pinches the wheel.
  - Hand moves arc around the gun instead of passing through it.
- **Office crying:** her right hand now presses to the bridge of her nose over her eyes, and her left hand stays near her lap. The old two-hands-on-face pose made the hands merge at her nose.
- **Time-lapse filing:** both hands hold the file overhand on the correct sides, so the arms no longer cross.
- **Mentor shielding (26.3–28.2 s):** his palms now face out towards her and his arms stay apart, no longer crossing. The directions are now set in his body space.
- **Hand audit** (`FrozenTearsGun_v001/scripts/hand_audit.py`, every 2 frames; checks hand vs hand, hand vs own torso/head, hand vs other character):
  - 5 samples remain, all explained in `review/hand_audit_v006.txt`.
  - Fingertip-in-gun samples: 5 single frames during fast moves.
- Sheet: `../FrozenTearsGun_v001/review/hands_v006_1persec.jpg`.

## Changes in v004 (look only)
- `pipeline/anim_look.py`: AgX Punchy, sky-gradient world for camera rays, saturation ×1.25, bump/normal ×0.35, roughness at least 0.35 on non-metals, f-stop at least 5.6, motion blur off, volumes halved, lights ×1.25.
- `FrozenTearsGun_v001/scripts/05_anim_look_fix.py`:
  - The explainer backdrop is now a sky-blue gradient (cyan at the top to near-white at the bottom), replacing the deeper teal.
  - The workshop window shows a daytime sky, and the workshop is high-key (brighter bulb, front wash, fill and rim, more world light).
  - Keyed light energies are ×1.25 and the keyed f-stop is at least 5.6.
  - The memory flashes are now short (+1.8 EV, 6-frame peaks), which fixes the blowout around frame 1700, and the office exposure is 0.
- Review sheet: `../FrozenTearsGun_v001/review/look_v006_1persec.jpg` (270×480, 8 samples).

## Changes in v003 (from v002)
- **Mentor's finale arms.** A natural brace replaces the T-pose: elbows bent, palms open, chin tucked. On the hit he flinches, then laughs and pats his chest.
- **Lecture.** He slaps the desk at 21 s and the papers jump. The camera drops into a low-angle push-in on him at 20.4 s.
- **Office dressing.** A city view outside the window (a cropped Poly Haven HDRI), a desk lamp with warm light, a second bookshelf and more books.
- **Realism pass.** The CO2 canister is now a lathed shape with a brushed finish; the workshop door is panelled with a knob; the pegboard has holes; the posters carry a blueprint grid. Box props are bevelled.
- **Clipping fixes.**
  - The funnel sits 16 mm off the cheek, and is still bone-parented to the head.
  - Grip fingers no longer sink into the wood.
  - The left hand arcs around the gun on its way to the valve.
  - The T-shirt and suit are pushed 3 mm out, so skin no longer pokes through at the shoulders.
  - At 25.4 s the camera no longer passes through her ponytail.
- **Audit** (`../FrozenTearsGun_v001/review/audit_v006.txt`, every 3 frames):
  - feet and camera clean
  - funnel 0 vertices inside the face
  - 3 single-frame fingertip contacts with gun parts (frames 340, 466 and 910, worst 9 mm, during fast hand moves)

## Known issues
- **Render cost.** The CO2 gas frames (about 7.4–12.6 s) are the most expensive, because of the small volume spheres seen through glass. A full gas frame (560) took 936 s (about 15.6 min) on this 4-core CPU, against an estimated 5–7 min for a typical frame. Test on the farm first (see SETTINGS.md).
- **Time-lapse (28.3–31.2 s).** Her pose snaps between three working poses on purpose (sketch, file at the vice, assemble), with no walking in between.
- **Crying face.** It uses the default rig's face bones (lids, brows, mouth corners, jaw). The ARKit expression pack isn't installed, so it is subtle rather than fully sculpted.
- **Hands and fingers.**
  - The fingers on the gun grip and the valve wheel are posed procedurally. They read correctly in the macro shots, but are not individually sculpted around every surface.
  - At the valve, one chamber drop sits 0.2 mm inside a fingertip at frame 349, which is not visible.
- **Mentor in the office (19.4–21 s).** The camera now drops into a low-angle push-in on him at 20.4 s.
- **Explainer backdrop.** This is the cyan gradient card behind the gun from 4.5 to 15 s. It sits just behind the gun, so the edge of the workbench shows in front of it in a few valve frames (6–7 s).
