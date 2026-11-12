# FanCancer_v002: farm package

This is the full 44.0 s film (frames 1–2640) at 1080×1920 and 60 fps, in the animated-CG look (client, Nov 11 22:45), ready for RenderStreet. No render has been submitted.

- `FanCancer_v002_60fps.blend`: the self-contained scene. Every texture is packed. It is compressed and stored as a normal git file (no LFS).
- `beats.json`: the 13 beat start frames at the target times. When the voiceover arrives, retime with `blender/pipeline/retime_to_vo.py`.
- `SETTINGS.md` covers the render settings and test frames, and `CREDITS.md` holds the CC-BY block for the video description.
- `package_check_lowres.jpg`: one low-res frame rendered from the packed file opened with `--factory-startup`.

**Voiceover:** none has been delivered yet. The film is built to the target beat times in `30_FanCancer.md`, so there is no mp3 in this folder.

**Source:** `../FanCancer_v001/scripts`. Build order:
1. `python3 -I 00_textures.py work`
2. `python3 -I 00_poster.py work`
3. `blender -b --python 01_build_humans.py -- work/humans.blend`
4. `blender -b work/humans.blend --python 00_build.py -- work/anim.blend anim`. This runs 02, 03, 03b, 04, `pipeline/anim_look.py` and 03c.
5. `06_package.py`

## Known issues
See `KNOWN_ISSUES` at the bottom of this file. They are filled in at packaging time.
