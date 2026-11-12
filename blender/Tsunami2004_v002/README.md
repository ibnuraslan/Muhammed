# Tsunami2004_v002: farm package

The full 40.0 s film (frames 1–2400) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `Tsunami2004_v002_60fps.blend`: the self-contained scene. Every texture is packed; it opens in factory Blender 5.2.2 with no add-ons.
- `beats.json`: the start frame of each of the 13 beats with its first words, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `SETTINGS.md`: render settings, measured cost and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_*.jpg`: low-res frames rendered from the packed file opened with `--factory-startup`. They show the package works; they are not quality references.

Source: `../Tsunami2004_v001/scripts`. Build order: `01_build_people.py` (needs MPFB2), `02_scene.py`, `03_anim.py` (runs `03_people.py`), `04_camera.py`, then `pipeline/package_for_farm.py`. `audit.py` is the contact/penetration audit; `audit_*.txt` holds its reports.

## Retiming to the VO
No voiceover yet; the film is built to the target beat times. When the mp3 arrives: `transcribe.py` → write anchors from `beats.json` (old frame per beat → the second its first word is spoken) → `retime_to_vo.py`. The camera is keyed on every frame, so the warp follows it exactly.

## Content notes (sensitive subject)
People are only shown confused on the exposed seabed and then running inland; every person leaves frame and is hidden before the wave reaches the beach. No bodies, no one is shown being hit. No text, logos or brand names anywhere.

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
