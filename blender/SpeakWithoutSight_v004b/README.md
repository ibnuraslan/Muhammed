# SpeakWithoutSight_v004b: farm package

This is the full 33.0 s film (frames 1–1980) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `SpeakWithoutSight_v004b_60fps.blend`: the self-contained scene, with every texture packed. Stored with Git LFS.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: the CC-BY block for the video description.
- `beats.json`: the 11 beat start frames for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `package_check_f780_lowres.jpg`: frame 780 at 25%, 6 samples, from the packed file opened with `--factory-startup` (no add-ons). It proves the file opens and renders; it is not a quality reference.

**No voiceover yet.** The director supplies the VO. To lay it in, run
`blender -b SpeakWithoutSight_v004b_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`,
building `anchors.json` from `beats.json` plus the word times from `pipeline/transcribe.py`.

The source is `../SpeakWithoutSight_v001/scripts` (`build.sh` rebuilds everything: 01 humans → 02 parlour → 03 animation + 03b FX/camera).
Review sheets are in `../SpeakWithoutSight_v001/review/`.

## Hand audit (BVH, every 2 frames, flagged = more than 8 hand vertices deeper than 5 mm)
- **About 1,094 flagged samples in this package, down from 2,767 at C.** This is an estimate: the girl, teacher and father counts come from the full run; the mother came from a separate mother-only run after her final fix, and that run doesn't check her hands against other characters. Files: `../SpeakWithoutSight_v001/review/D_hand_audit_full_prev.txt` and `D_hand_audit_mother_final.txt`.
- **Mother: 0**, after spreading her hands and lifting them off her lap.
- **The rest:**
  - Deliberate contact: the girl's hand on the teacher's throat, lips and nose (Tadoma, about 300 samples), and her own hand on her own lips and throat.
  - The girl's lap hand resting on her skirt drape (about 430 samples), a few millimetres deep.
  - The teacher's hands near each other during the gasp, and on her thigh and heart (about 200 samples).
  - None are joints bent the wrong way: Limit Rotation constraints sit on every finger, thumb and wrist bone.

## Known issues
- **Look.** This is the animated-CG look ordered by the client at 22:45: AgX Punchy, high-key, a sky-blue explainer dome, and clean cream and pink anatomy.
- **No voiceover yet.** Beats sit on the target times in the brief. Retime with `beats.json` when the VO arrives.
- **Lip touches (beats 7–9)** use a Tadoma hold, with the fingers resting on the lips and nose. The fingertip pad sits within about 1 cm of the surface, with a 2.5 mm skin press. The audit counts these deliberate contacts as shallow overlaps.
- **Wrist grip (7.5–8.6 s).** The teacher's fingers wrap the girl's wrist. Some finger vertices overlap the girl's wrist by 6–10 mm; this reads as a firm grip in close-ups.
- **Ending changed.** The hug was dropped: it produced about 500 overlapping vertices that couldn't be fixed in time. The film now ends with the girl speaking, her hand on her own throat, and the teacher gasping, then putting her hand on her heart. The family reacts, and the dog wags.
- **Mother stays seated** at the end. Her seated skirt drape doesn't support standing up.
- **The teacher's skirt** switches to the leg-wrapping drape at frame 399, as she kneels, while the room is dim.
- **Mixed models.** Characters are MPFB humans. The hand skeleton, larynx, footstool, open book and dog are CC-BY Sketchfab/Objaverse models (see CREDITS.md). Everything else is Poly Haven CC0.
