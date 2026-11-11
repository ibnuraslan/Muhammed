# SurgeonBrandsLivers_v002: farm package

This is the full 28.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `SurgeonBrandsLivers_v002_60fps.blend`: the self-contained scene, 62 MB, committed as a normal git file (studio policy: no LFS). Every texture is packed inside, and it opens in factory-startup Blender 5.2.2.
- `beats.json`: the beat start frames and first words, for the voiceover retime (`pipeline/retime_to_vo.py`).
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_f1128_lowres.png`: a 20 %, 4-sample frame from the packed file in factory Blender. It shows the package works; it is not a quality reference.

The source is `../SurgeonBrandsLivers_v001/scripts`. To rebuild, run `build.sh` (01 → 04), then `05_package_prep.py` and `pipeline/package_for_farm.py`. Review sheets and the audit are in `../SurgeonBrandsLivers_v001/review/`.

## Beats (base timing)
| # | Frame | Line | Picture |
|---|---|---|---|
| 1 | 1 | During a transplant… burn his initials into the… liver | OR crane down, then a dive through the skin into the cyan studio. The pen burns SB *into* the liver surface: a dark seared line with a glowing edge only at the tip, plus sparks and smoke |
| 2 | 301 | Then he stitched her up and acted like nothing had happened | rise out to the sutures, then the mask comes down to a smirk |
| 3 | 565 | a week later | whip-pan to the wall calendar, pages flip |
| 4 | 637 | the new liver started to fail | through the wall into her living room: she drops her mug and doubles over, and the x-ray liver turns blue to red |
| 5 | 781 | She went back into surgery, but this time with a different doctor | the bed bursts through the OR doors, and surgeon 2 walks in snapping her gloves |
| 6 | 1045 | who soon found the initials inside | dive again: gloved hands lift the liver and the SB brand is revealed; her eyes widen over the mask |
| 7 | 1231 | The surgeon admitted it wasn't the first time he'd branded a patient | whip into the hearing room past glowing ghost livers to the confessing surgeon |
| 8 | 1501 | and he eventually lost his medical license | the gavel slams, a red seal is stamped on the licence, slow push and settle |

## Known issues
- **No voiceover yet.** Timing follows the brief's target times. Retime once the VO is in.
- **Transit wipes.** The camera never sits inside a slab. On the dives and rises it passes through the abdomen skin and a tissue membrane: 4–5 skin frames + 4 membrane frames per dive (about 0.15 s). Wall fly-throughs show 1–3 frames of tile or panel texture. The camera jumps across the slab between two of those textured frames. Motion blur is set to start-on-frame, so the jump does not smear.
- **Pick-ups.** For about 20 frames while the gavel and stamp are picked up, the finger base is 9–12 cm from the grip point (the wrist is on target). The PanelA gavel grip reads a little stiff.
- **Feet.** Surgeon 2's left foot slides about 0.1 m/s for about 4 frames as her walk settles (f994–997).
- **Off-camera teleports.** Surgeon 1, the patient and the nurse move between sets while the camera is in another room. The audit ignores these moments.
- **Smirk.** Surgeon 1's smile is subtle. The MakeHuman face rig has no expression shape keys, so it is bone-driven.
- **Caps and masks.** These are simple modelled shells. They don't simulate cloth.
