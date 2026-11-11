# SwedishCoffee (Connect27)

A 44.5 s vertical true-story short: the 18th-century Swedish king who "tested" coffee on twin prisoners. One continuous camera, 1080×1920, 60 fps, frames 1–2670.

## Files
- `SwedishCoffee_v00N_60fps.blend`: packed farm file (see `SETTINGS.md`). Opens in factory Blender 5.2.2.
- `beats.json`: the 13 beat start frames, built to the target times in `briefs/27_SwedishCoffee.md`. When the VO arrives, retime with `pipeline/retime_to_vo.py`.
- `CREDITS.md`: every model and texture, plus the CC-BY block for the video description.
- `scripts/` (in `SwedishCoffee_v001/`): `01_cast.py` builds the MPFB cast; `02_build.py` builds the whole film (sets, animation, camera); `lib.py` has the helpers; `audit.py` is the contact audit; `frames.py` renders review stills.
- No VO mp3 yet: the brief uses our script with no narration delivered. Retime when it lands.

## How the one camera works
The film is eight sets (courtyard → throne hall → street → castle chamber → snowy churchyard → masked ball → bedroom → town square). Each set sits on a root placed so that its entry portal lines up exactly with the previous set's exit portal. The single camera is a Catmull-Rom spline through about 75 framings (one every 0.5–1.2 s), baked to every frame. Set changes happen while the camera physically passes through something:
- a house window (courtyard→palace, street→chamber)
- the coffee steam / skull (throne hall→street)
- an open window (chamber→churchyard, bedroom→square)
- the church façade (churchyard→ball)
- a doorway (ball→bedroom)

The sets are shown and hidden with `hide_render` keys at those frames.

## Known issues
See the checkpoint messages; the current list is kept at the bottom of this file at packaging time.
