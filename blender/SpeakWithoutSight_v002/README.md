# SpeakWithoutSight_v002: farm package

This is the full 33.0 s film (frames 1–1980) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `SpeakWithoutSight_v002_60fps.blend`: the self-contained scene, with every texture packed. Stored with Git LFS.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: the CC-BY block for the video description.
- `beats.json`: the 11 beat start frames for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `package_check_lowres.jpg`: a low-resolution frame from the packed file opened in factory Blender. It proves the file opens; it is not a quality reference.

**No voiceover yet.** The director supplies the VO. To lay it in, run
`blender -b SpeakWithoutSight_v002_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`,
building `anchors.json` from `beats.json` plus the word times from `pipeline/transcribe.py`.

The source is `../SpeakWithoutSight_v001/scripts` (`build.sh` rebuilds everything: 01 humans → 02 parlour → 03 animation + 03b FX/camera).
Review sheets are in `../SpeakWithoutSight_v001/review/`.

## Known issues
KNOWN_ISSUES_PLACEHOLDER
