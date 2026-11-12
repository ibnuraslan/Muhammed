# FanCancer_v003: farm package (acting pass on approved v002)

This is the full 44.0 s film (frames 1–2640) at 1080×1920 and 60 fps, in the animated-CG look (client, Nov 11 22:45), ready for RenderStreet. No render has been submitted.

- `FanCancer_v003_60fps.blend`: the self-contained scene, (size: see the commit message). Every texture is packed. It is compressed and stored as a normal git file (no LFS). Checked in `--factory-startup`: 0 unpacked images, one camera (`FilmCam`), frames 1–2640, 60 fps, AgX Punchy, motion blur off.
- `beats.json`: the 13 beat start frames at the target times. When the voiceover arrives, retime with `blender/pipeline/retime_to_vo.py`.
- `SETTINGS.md` covers the render settings and test frames, and `CREDITS.md` holds the CC-BY block for the video description.
- `package_check_lowres.jpg`: frame 2460 at 25 % and 8 samples, rendered from the packed file opened with `--factory-startup`.
- Acting review: `../FanCancer_v001/review/ACTING_notes.md` (fix list), `ACTING_before_0.5s.jpg`, `ACTING_after_0.5s.jpg`, `ACTING_hand_closeups.jpg`, and `qa_v003.json` (director `qa_check.py`).

**Voiceover:** none has been delivered yet. The film is built to the target beat times in `30_FanCancer.md`, so there is no mp3 in this folder.

**Source:** `../FanCancer_v001/scripts`. Build order:
1. `python3 -I 00_textures.py work`
2. `python3 -I 00_poster.py work`
3. `blender -b --python 01_build_humans.py -- work/humans.blend`
4. `blender -b work/humans.blend --python 00_build.py -- work/anim.blend anim`. This runs 02, 03, 03b, 04, `pipeline/anim_look.py` and 03c.
5. `06_package.py`

## Known issues
- **Textures:** packed at 512 px (hero skin diffuse at 1K, normal and roughness maps at 256 px) to fit the 95 MB limit. This suits the clean animated look; very close macro shots of fabric are soft.
- **Hand audit:** 655 BVH hits remain (0 hand-to-hand). Most are a constant 21–23 triangle overlap between the right wrist and MPFB clothing skinned to it; it does not show in the close-ups. Report: `../FanCancer_v001/review/C_hand_audit_pre_fix.txt` (despite the name, this is the post-fix run).
- **Beat 5 (13–15 s):** she bows over the phone, so the blurred note shows at an angle. The screen is double-sided; the side the manager sees is mirrored and unreadable by design.
- **Beat 10 (31–32 s):** the set change runs through the clinic's ceiling diffuser panel. That frame is bright but carries a prismatic grid.
- **City:** a single Objaverse building is repeated, with randomly lit windows. The phones there are cards on the bus riders and in windows.
- **Crowd:** FK keys every 0.5 s with eased interpolation. Skaters glide on FK legs, which is intended on ice. Hockey sticks were removed because they floated near the hands.
- **Faces:** expressions are keyed on the MPFB face bones (brows, lids, jaw, lips) for the fan, manager, doctor and the crowd's cheer. They are mild at thumbnail size on distant crowd members.
- **Voiceover:** none yet. The film is timed to the brief's target beats (`beats.json`).
