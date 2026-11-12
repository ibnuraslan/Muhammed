# SwedishCoffee (Connect27)

Current package: `blender/SwedishCoffee_v005/SwedishCoffee_v005_60fps.blend` (72 MB, normal git): the acting pass on v004 (approved). Every story-beat frame in `beats.json` is unchanged. The full list of fixes, with frames, is in `SwedishCoffee_v001/review/ACTING_notes.md`. In short:
- the three wall fly-throughs and the doorway pass are now open-air whip-pans, and set swaps happen earlier so every beat frame shows its subject
- servants really pour into the resting cup between sips
- coffins are hand-carried at hip height
- the ball has dancing couples hand in hand
- at the bedside twin A's hand rests on his brother's hand
- the king's fall reaches out with both hands and lands with his hands flat on the floor
- idle hands sit clear of hips and coats

v002–v004 are kept.

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

## Look
The bright animated-3D look follows `blender/STYLE_ANIMATED.md`: `pipeline/anim_look.py` is applied on top of the build (AgX Punchy, sky gradient for camera rays, saturation up, bump down, roughness ≥ 0.35, f-stop ≥ 5.6, motion blur off). Interiors are clean cream / pale-blue plaster with soft ceiling area lights. Costumes are saturated period colours (blue-and-gold guards, a royal-blue king, coloured townsfolk).

## Hands
- Every character has Limit Rotation (local) on the fingers (0–90° forward curl, no backward bend, ±10° spread), the thumbs and the wrists (±60° flex, ±25° twist).
- Idle hands carry a relaxed curl.
- Cups are held beside the index knuckle with curled fingers. The cup follows a hold point computed from the knuckles every 5–6 frames.
- Close-ups of all 18 hand actions: `SwedishCoffee_v001/review/D_hand_closeups.jpg`.
- Hand audit (BVH, every 2 frames), v003: `SwedishCoffee_v001/review/D3_v003_hand_audit.txt`. HAND_OTHER 0 and JOINT_BACK 0.
  - HAND_HAND 10: the soldier's two hands meet on the coffee pot he smashes (intended two-handed grip).
  - HAND_TORSO 402 (down from 2176): idle hands of background characters touching the coat skirt at the hip, mostly the two scaffold guards (S1) and the coffin bearers' outer hands. These are fingertip contacts with the coat, not hands through the body. Each one needs the hand moved ~3 cm out.

## Known issues
- The skull in the steam (b3, 7.8–9.6 s) reads as a pale skull in mist; density is doubled to survive the look pass.
- The churchyard (b9): the cathedral walls now read as light stone, but the roof band of the Sketchfab model (its `RooftilesWood` and `BrickOldRounded` materials) still renders black at 28–31 s. These didn't fix it: overriding the base colour, removing the normal/metal/alpha links, turning off backface culling, and adding interior lights. The next thing to try is replacing those faces' material outright, or hiding the roof and adding our own slate roof.
- The bed curtains and canopy (b11) are simple velvet panels, not cloth-simulated drapes.
- The window curtains and bed curtains are subdivided velvet panels with a light wave fold, not cloth sims, so they read as soft slabs.
- Set changes are passes through a façade, wall or steam. The wall fills the frame for about 5–6 frames at 2.8 s, 12.0 s and 31.0 s (the 12.0 s still lands on one of them).
- MPFB garments are recoloured as period coats; collars and cuffs still have a modern cut up close. The king now has powdered long hair (MPFB long01, desaturated and lightened) instead of the cap-like wig model; there's no ermine (the capelet test read as white patches and was removed).
- The king's collapse (b10) is keyframed: an eased knee buckle, then a fold to the floor. It isn't a physics fall.
- The servant's hand rests on top of the pouring pot (the pot hangs from the wrist) rather than wrapping its handle. The toast cups in the square sit at a tilt in the hand.
- Cups: the handle of the cup model doesn't point into the fingers; the cup is held by the body and saucer.
- No VO yet. `beats.json` is at the brief's target times; retime with `pipeline/retime_to_vo.py`.
