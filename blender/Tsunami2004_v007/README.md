# Tsunami2004_v007: farm package (director review of v006)

The full 40.0 s film (frames 1–2400) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `Tsunami2004_v007_60fps.blend`: the self-contained scene. Every texture is packed; it opens in factory Blender 5.2.2 with no add-ons.
- `beats.json`: the start frame of each of the 13 beats with its first words, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `SETTINGS.md`: render settings, measured cost and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_*.jpg`: low-res frames rendered from the packed file opened with `--factory-startup`. They show the package works; they are not quality references.

Source: `../Tsunami2004_v001/scripts`. Build order: `01_build_people.py` (needs MPFB2), `02_scene.py`, `03_anim.py` (runs `03_people.py`), `04_camera.py`, then `pipeline/package_for_farm.py`. `audit.py` is the contact/penetration audit; `audit_*.txt` holds its reports.

## Retiming to the VO
No voiceover yet; the film is built to the target beat times. When the mp3 arrives: `transcribe.py` → write anchors from `beats.json` (old frame per beat → the second its first word is spoken) → `retime_to_vo.py`. The camera is keyed on every frame, so the warp follows it exactly.

## Content notes (sensitive subject)
People are only shown confused on the exposed seabed and then running inland; every person leaves frame and is hidden before the wave reaches the beach. No bodies, no one is shown being hit. No text, logos or brand names anywhere.

## v005 changes (client acting review, Nov 12)
Acting pass on the approved v004; every story-beat frame unchanged (beats.json identical). Full list with frames: `ACTING_notes.md`.
- Natural arm hang/swing (no arms held out sideways), runners' arms clear the hips.
- No frozen stands: breathing, weight shifts, head scanning on every standing person; head steady while shading the eyes.
- Kids walk over to the adults and point instead of a 5 s freeze; realistic first stride instead of an 11 m/s sprint at 12.4 s.
- Beat 4 (7.2 s): camera faces the group so faces read.
- No black frame on the seabed exit (15.5 s); stall-sign glyphs removed; flat sun loungers removed; runners exit past the hotel; hotel spray resized; camera keeps clear of the mosque wall.
Checks: `clip_scan_v005.json` (director clip_scan.py, step 6, 2 cm): **0 bad ranges**. `hand_audit_v005.txt` (stricter, any BVH contact, every 2 frames): hand–hand 0, hand–other 0, hand–head 1, hand–torso 11 (runner's hand brushing the hip at 18.4–21.3 s), hand–clothes 264 (sub-centimetre touches of relaxed hands on shorts/shirt hems, none >2 cm per clip_scan).
Sheets: `before_v004_0.5s_part1/2.jpg`, `after_v005_0.5s_part1/2.jpg`, close-ups `hand_closeups_v005.jpg`.

## v005 changes (director, wave review)
1. Hero wave 15.6–21.0 s: a dedicated curling mesh (profile with overhanging lip, ~21 m crest, 320 m along the shore) with noise displacement, translucent teal face streaked with foam into a white crest, 400 spray droplets off the lip, boats/palms/car in the face. It advances with the old sheet hidden; the GN sheet returns as the breaking bore at 21.06 s. Camera grows the wave from the seabed (15.6–17.5) then sits at ground level among the umbrellas looking up as people run toward it (18.3–20.3).
2. 11.8–12.8 s: tourists stand on the seabed pointing at the wave forming on the horizon (long lens over their shoulders); the camera then dives through the sea floor into the cross-section (the studio bowl now sits under the exposed seabed).
3. Flood: Ocean modifier (small-scale displace) on the flood surface, darker brown-teal, foam only on the front/steep edges and as long current lines (no cloud patches), debris riding.
4. Camera clamped ≥ 0.7 m above ground outside the dive.

## v003 changes (director D review)
1. Cross-section: clean colour-coded strata (sediment yellow, crust orange/brown, ocean crust blue-grey, glowing mantle) with wavy layer boundaries; seaward plate drops, water column dips (sucked back) then bulges; yellow energy-pulse arrows run out both ways.
2. Wave 16–18 s: camera 10–12 m from the face with a 16 mm lens, so the wall fills the frame; palms bend inland before the wave arrives; boats/palms/car ride the face.
3. Empty beats: tighter lenses on the kids and the fisherman walking out at 1–4 s, extra stranded fish along their path; the aerial at 11–13 s looks at the horizon wave instead of open water.
4. Flood: brown-teal water, stronger churn displacement, foam stretched into lines along the current, 30 extra cars/umbrellas/boats tumbling along the camera street.
5. Aftermath 35–40 s: tight crane around the standing mosque with 45 extra debris pieces.
(Audit files are from v002: people/hand animation is unchanged in v005.)

## Look
Bright animated-CG look per `blender/STYLE_ANIMATED.md` (client, 22:45 UTC): `pipeline/anim_look.py` is the last build step, plus hand-tuned sky-blue studio bowl, clean cyan wave with white foam, teal flood, bright late-afternoon ending.

## Audits (packed build)
- `audit.txt` (every 6 frames): FOOT_HOVER 4 (3–7 cm, runners decelerating at the end of the run at 20.8–21.1 s and the fisher's step-turn at 9.3 s), PERSON_PERSON 1, everything else 0 (no slides, no hands through props, camera never inside geometry or under water).
- `hand_audit.txt` (every 2 frames, people in view): hand–hand 0, hand–torso 0, hand–head 0, HAND_CLOTHES 45, HAND_OTHER 1. The clothes hits are single-triangle fingertip grazes against shorts/shirt hems in the relaxed hanging pose (checked in close-up: no visible pass-through). Limit Rotation on all finger/thumb/wrist bones; relaxed curled default; the fish is gripped by the tail.
- `hand_closeups.jpg`: 270×480 close-ups of every hand action.

## Known issues
- The wave is a shape-keyed sheet, not a fluid sim; its crest spray is a volume shell (seen best at 16–21 s).
- Crowd clones (12) are time-shifted copies of the 8 performers, so some gestures repeat at a distance.
- Fingertip grazes on clothes as listed above; a few distant feet 3–7 cm off the ground while running.
- The dive through the sea surface (12.95–13.1 s) is a near-full-frame water surface for about 8 frames (ripple detail, no blank colour).
- Textures were downsized to 512–1024 px and re-encoded as JPEG to keep the file under 95 MB.

## v006 changes (moving-preview review, Nov 14)
Made from v005 after watching the moving preview (`blender/pipeline/preview.py`, every 5th frame). The beat frames are unchanged and `beats.json` is identical. `review/preview.mp4` is the moving preview (every 5th frame, 12 fps, 270×480) of this packed file. There were three v006 builds, and only the fixed section differs between them. The builds are seeded, so every other frame is identical. The preview frames come from: frames 1051–1291 from the final build; 886–960 and 1292–2400 from the second; the rest from the first. One check frame (451) was re-rendered from the final file and compared to confirm.
- Stranded fish now lie on the sand. They used to hover 5–9 cm above it, and their flapping hops are now 3–7 cm high.
- The wet sand is rougher and less shiny, so the low sun no longer blows out into a beige blur (around 11.0–12.2 s and 17.8–18.1 s).
- Earthquake cross-section: the camera holds the level cross-section view from 15.0 s. At 15.6 s (beat 7) it goes in one frame to the beach, at the moment the wave appears; the cross-section and the hero wave now switch on that same frame. This removes the tilted box in a grey void (15.17–15.5 s), the dark frame under the sea floor (15.58 s) and a wave popping in after the cut.
- A runner (LocalM) passed right in front of the lens at 18.15 s. He is now hidden from 13 s, while off screen.
- Checks on the packed file: clip_scan 0 bad ranges. qa_check shows EMPTY 298 and INSIDE 11, both intended (see ACTING_notes.md). Nothing is unpacked, there is one camera and output is PNG. The file is 85 MB.

## v007 changes (director review of v006, Nov 14)
Beat frames are unchanged and `beats.json` is identical. `review/preview.mp4` is the moving preview of this packed file (every 5th frame, 12 fps, 270×480; pages p01–p10). Frames 1–1235 come from the first v007 build. The last fix changed only flood-time objects and material keys (after 20.6 s), so frames 1236–2400 were re-rendered from the final package.
1. Into the cross-section: the camera holds the horizon view from 12.95 s, then cuts cleanly at beat 6 (13.1 s) to a tight, level view of the cross-section with no backdrop edges and no grey void. A slow push-in runs until the clean cut out at 15.6 s (beat 7), where the beach view and the wave appear on the same frame.
2. 2.5–4 s: the camera looks more level, so the receding sea stays on the horizon behind the fish and the seabed.
3. 9.2–12.4 s: the high aerial drift is gone. A low three-quarter camera stays clear of the group: the fisher waving and shouting inland (his face shows on beat 5), the kids pointing, everyone turning to run.
4. The diagram never holds static (slow push-in).
5. Flood:
   - Muddy brown water, roughness 0.5, so there are no sun-glare blobs.
   - 72 floating debris pieces instead of 30 (cars, boats, umbrellas) along the camera path. The extra pieces use their own random stream, so the collapsing houses, poles and wires keep their checked layout.
   - The camera is aimed higher at the town, so water fills less of the frame.
- Checks on the packed file: clip_scan 0 bad ranges. qa_check shows EMPTY 277 only (intended, see ACTING_notes.md). Nothing is unpacked, there is one camera and output is PNG. The file is 85 MB.
