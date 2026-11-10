# GoatRescue2_v002: farm package (retimed to the voiceover)

This is the full 35 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `GoatRescue2_v002_60fps.blend`: the self-contained scene. Every texture and the voiceover are packed inside.
- `GoatRescue2_v002_VO_Marcus.mp3`: the narration. Lay it at frame 1 when encoding.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_f700_lowres.png`: a 20 %, 4-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

The source is `../goat_rescue2_v001/scripts`. Build order: 01, 01b, 02, 03 (which runs 03c and 03b), then 05_retime_to_vo.py.
05_retime_to_vo.py warps every keyframe so that each story beat starts on its word in the voiceover. Word times come from faster-whisper.

## Known open items
- Medics are already crouched when they first appear; there is no walk-up.
- On slopes, some hooves are 2–5 cm off the ground, and a few fingertips dip into the manure.
- The X-ray shows the femur and pelvis only.
