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

## Known issues
(see bottom, updated at packaging)
