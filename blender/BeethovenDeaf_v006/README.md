# BeethovenDeaf_v006: farm package (animated look; supersedes v005)

## Changes from v005 (client look change, Nov 11 22:45 UTC: bright, clean 3D animation, not a film)
v005 was run through `pipeline/anim_look.py`, then hand-tuned with `BeethovenDeaf_v001/scripts/07_anim_look_fix.py`. Animation, geometry and camera path are unchanged.
- **Colour:** AgX Punchy at exposure +0.25. Material saturation ×1.25, bump and normal ×0.35 (×0.5 again on the skin), roughness at least 0.35.
- **Room:** candlelit but warm, bright and readable. A large soft high-key fill was added, the fills and candles are 1.6–3.5× brighter, and shadows are lifted.
- **X-ray backdrop:** sky gradient, light blue at the bottom to cyan-blue at the top, pre-compensated for AgX desaturation. It replaces the navy/teal.
- **X-ray clean-up:** the skull is nearly clear (97 %) over the ear macros, so there is no grey veil. The fully ghosted body is hidden f640–1150, when it is invisible anyway; its stacked transparency had been greying the backdrop.
- **Camera:** f-stop never below 5.6 (macro shots keep f/8–11), so backgrounds stay readable. Motion blur is off.
- **Rings and pulses:** saturated cyan and red, so they read on the light backdrop.
- **Transparent bounces:** raised to 32.

## Changes from v004
The procedural ear-canal half-pipe has been removed, because the client wants no illustrated shapes. Every visible ear part is now from the real anatomical model (osuecampus, CC-BY): the eardrum, the ossicles, the labyrinth with the cochlea, and the nerves. The red 'normal path' pulse still runs in through the ghosted skin and dies on the torn eardrum; see `../BeethovenDeaf_v001/review/v006_canal_check.jpg`.

## Changes from v003 (carried into v004/v006)

- **X-ray look:**
  - The studio backdrop is a vertical navy → deep cyan → navy gradient, dark at the top and bottom of the frame, on a smooth sphere.
  - The skull has a cyan fresnel rim and 15 % translucency through the dive, rising to 86 % for the ear macros. The skull glow is a cyan wavefront.
  - The cutaway is saturated: gold ossicles, yellow nerves, a blue labyrinth with a cyan-lit cochlea that warms to white-gold on "so he could still hear", and the grey torn eardrum.
- **Hair:** wild clumped strand locks (420 guide hairs × 40 clumped children), swept back and up, with per-strand grey variation. It replaces the earlier puff.
- **Keys:**
  - The model's fused keys were replaced by 88 separate hinged keys (52 ivory, 36 ebony).
  - The 48 keys that are struck go down 9 mm at the front edge on each strike, about 2000 keyframes in all, and the fingertips ride them down.
  - The hands sit so the strikes land on the front of the white keys.
- **Strikes:** a final strike pass now runs after the in-between fixes. All 256 strikes are within 9 mm of the pressed key top, mean 2 mm; previously 4 hovered by up to 19 mm.

This is the full 26.5 s film at 1080×1920 and 60 fps (frames 1–1590), ready for RenderStreet. No render has been submitted.

- `BeethovenDeaf_v006_60fps.blend`: the self-contained scene. Every texture is packed, and it opens in factory-startup Blender 5.2.2.
- `beats.json`: the beat start frames for the voiceover retime.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description.
- The 0.2 s sheets of this exact packed file, rendered in factory-startup Blender, are `../BeethovenDeaf_v001/review/v006_polish_0p2s_a/b/c.jpg`, and the director's mini sheet is `v006_mini_sheet.jpg`.

The source is in `../BeethovenDeaf_v001/scripts`. Run `build_all.sh <work_dir>`: it fetches the assets, then runs 01 to 05 and the audit in 06.
Review sheets and the audit are in `../BeethovenDeaf_v001/review/`.

## Story beats (target times from the brief; there is no VO yet)
| # | Frame | Line starts | Picture |
|---|---|---|---|
| 1 | 1 | He would bite down… | Macro of the teeth clamping the brass rod; profile; pull back along the rod into the candlelit room |
| 2 | 235 | …as he played | Hands crash on the keys; low camera on the keys |
| 3 | 313 | The piano's vibrations… | Cyan rings run up the rod; the camera rides beside them |
| 4 | 517 | …into his jawbone… | X-ray: skin to glass, the room dissolves into a cyan studio, rings run through the mandible |
| 5 | 715 | This sent the sound… | Glow wave over the skull; orbit; ear cross-section |
| 6 | 985 | …skipping his damaged eardrums… | Torn grey eardrum; a red pulse dies on it; cyan rings bypass it |
| 7 | 1105 | …so he could still hear | Cochlea lights from cyan to warm white; pull out to his face as his eyes close |
| 8 | 1207 | And by using this trick… | Passionate playing, pages fly, spiral crane up to top-down |

## Voiceover
None has been delivered. When it arrives:
1. Run `pipeline/transcribe.py` to get the word times.
2. Build `anchors.json` from `beats.json`: old frame → the second of each beat's first word.
3. Run `blender -b BeethovenDeaf_v006_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 BeethovenDeaf_v003_60fps.blend`.
4. Re-pack with `package_for_farm.py`.

The X-ray fades, glow radii and ring paths are all ordinary keyframes, so they warp with everything else.

## Known issues
- **No VO yet.** The timing follows the brief's target beat times (±0.3 s); a retime is needed when the VO arrives.
- **Fingertip dips:** in 5 in-between frames a fingertip dips 8–16 mm under a key top: f167, f203–205, f649 and f743. The last two are during the X-ray, when the hands are invisible.
- **Black keys:** they are never struck; all strikes land on white keys.
- **Cravat:** it is the suit's tie region recoloured to dark red silk, with the suit's own stripe shading, rather than a separately modelled neckcloth.
- **Ear scale:** the ear cross-section (eardrum, ossicles, labyrinth) is scaled about 2.5× life size so it reads in vertical frame. There is no canal geometry; the pulse runs through the ghosted skin.
- **Skull:** it is one rigid mesh that follows the head bone. Its jaw does not open with his (the jaw is nearly closed on the rod during the X-ray, so this does not show).
- **Hair:** the strands have only been checked at 270×480 and 8 samples, so check frame 40 on the farm. Hair render cost is moderate.
- **Room hidden during the X-ray:** the bench, piano and music desk are hidden by keyframe from f629 to f1137, while the opaque studio backdrop surrounds the head. Nothing outside the backdrop is visible then. The keys stay visible, but the backdrop occludes them.
