# DrunkTrain_v002: farm package

This is the full 34.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `DrunkTrain_v002_60fps.blend`: the self-contained scene. Every texture is packed inside.
- `beats.json`: the start frame of each of the 12 beats, for `pipeline/retime_to_vo.py` once the voiceover arrives. There is no VO yet: the film is built to the brief's target beat times.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `review/`: 0.2 s polish sheets and the audit report.

The source is `../DrunkTrain_v001/scripts`. Build order: `01_build_people.py`, then `02_build_scene.py`, then `03_animate.py` (which runs `03b_fx_camera.py`). `04_audit.py` is the contact and penetration audit.
