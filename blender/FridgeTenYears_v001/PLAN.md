# B11 FridgeTenYears: Phase 1 plan (Connect B11)

**Reference:** `briefs/batch2/B11_FridgeTenYears_reference_1fps.jpg` (current style, 34 s). We follow its order: the man going behind the cooler bank, the man stuck in the gap, cooler fronts ("noise of the coolers"), two men talking in the store (days → months, no leads), the empty store ten years later, contractors in orange shirts and yellow hard hats pushing the unit, then the skeleton. The risky parts are re-staged (see below).

**Format:** 1080×1920, 60 fps, Cycles. Hard cuts: one camera per shot, switched by timeline markers. Every key is LINEAR (dense keys from functions), so nothing interpolates across a cut.

**Set:** the BellyFat_v010 supermarket shell (floor, walls, ceiling tubes, stocked gondolas), with the ceiling raised 1 m, plus a new bank of three glass-door reach-in coolers (2.15 m tall) built for this film. Each unit has:
- three glass doors with frames and chrome handles
- five shelves of generic bottles, cans and cartons (no text or brands)
- LED mullions and a blank lit header
- a kick-plate grille, copper coil on the back, and a condensing unit with a spinning fan on top

The bank stands **48 cm off the back wall**, and that gap is where he falls. Two eras:
- **2009:** bright, warm, fully stocked, three units, boxes stored on top.
- **2019:** the same room with empty gondolas, light at 55% and cooler in colour, flattened boxes on the floor, the two side units gone (floor marks where they stood), and only the hero unit left.

**Characters** (MPFB rigs from finished films, re-dressed; all have the eye fix on every EnhancedEye group, hand limits, the elbow IK limit opened to −40°, and a ≤1.2 W camera catchlight on face shots):

| Name | Source rig | Look |
|---|---|---|
| Worker (victim) | BellyFat ShopperA | neon yellow-green shirt, blue jeans (the reference's look) |
| Manager | RingBullet Owner | dark suit and tie |
| Detective | GoatOwner OffA | royal-blue shirt, dark jeans, fringe lifted off the eyes |
| ConA | WaterTubes Hero | safety-orange long-sleeve top, charcoal work trousers, yellow hard hat, **DA KRAS FILMS on the back** |
| ConB | DrunkTrain Worker | orange overalls, orange tee, yellow hard hat |

**Props:**
- a hard hat (Sketchfab CC-BY, Kristiyan Marinov), bone-parented to the head
- a skeleton (Sketchfab CC-BY, Ruslan Gadzhiev), recoloured clean cream bone

No held props anywhere in the film.

**Clips:** each shot is its own 1× clip, about 30% longer than the expected beat (`scripts/03_anim.py`, `SHOTS` table). Phase 2 lays them on the VO frames (`timing.json`) and trims the tails only. No time-stretching.

| Shot | Beat (reference words) | Who and what they physically do | Camera | Clip (f) |
|---|---|---|---|---|
| S01 | A man… | Worker walks carefully along the top of the cooler bank (boxes stored up there), arms swinging, looking at his footing. | High ¾ front from ahead of him, 32 mm, slow drift | 117 |
| S02 | …fell behind a refrigerator unit | He turns to face the store and takes small steps back toward the wall. His heel goes off the back edge, he tips back with his arms flying up, and drops **feet-first** into the 48 cm gap. | High, in front and above the bank, tilting down into the gap opening, 28 mm | 117 |
| S03 | …at the supermarket where he worked | Crane from the stocked aisle up over the cooler bank. He is wedged upright in the gap, face up, arms reaching (no contact). | 24 mm crane up | 156 |
| S04 | …in 2009 | Wide from above the gap: him wedged, looking up, calling | 26 mm from above, push | 117 |
| S05 | Seriously trapped | Closer from above: twisting, arms waving up | 40 mm from above | 78 |
| S06 | …but his cries for help… | CU of his face from directly above, calling (mouth slightly open, no teeth grimace), one hand waving | 55 mm from above, push-in | 156 |
| S07 | …were drowned out by the noise… | Glass-door cooler fronts, lit and stocked (he is behind them, unseen) | 30 mm lateral push along the doors | 117 |
| S08 | …of the coolers | The condensing unit on top, fan spinning behind its grille | 45 mm f/9 push-in | 117 |
| S09 | Days passed… | The store manager and a detective walk in from both sides and meet in front of the coolers | 26 mm, slow push | 117 |
| S10 | …and weeks turned into months… | They talk. The manager speaks (jaw) and nods; the detective shakes his head. | ¾ on the manager's face, 35 mm | 156 |
| S11 | …with no leads… | The manager shrugs, both palms forward and open at waist height; the detective nods | ¾, 35 mm | 117 |
| S12 | …on his whereabouts | The detective turns and looks round the store. The camera rises toward the cooler-bank top (irony: he is right there). | 28 mm rise | 156 |
| S13 | Ten years later… | The same store, abandoned: empty gondolas, dim cool light, debris, the lone cooler at the end | 24 mm push down the aisle | 156 |
| S14 | …contractors began working… | ConA and ConB walk down the aisle toward the cooler, arms swinging | 32 mm, front, backing up | 117 |
| S15 | …on the now abandoned supermarket | At the cooler: ConA points at it, ConB nods | 30 mm ¾ | 117 |
| S16 | As they moved… | Both push the unit's side panel with palms flat (`hold_flat_object`, 14 mm off the enamel). The unit slides along the wall. **Logo on ConA's back**, ¾ so his profile reads. | 30 mm ¾ from behind | 156 |
| S17 | …the refrigerator unit… | Wide: the unit keeps sliding, and the gap behind it opens | 26 mm | 117 |
| S18 | …they found… | They straighten, step back from the panel and turn their heads to stare into the gap | From the gap end (open, side units gone), faces toward the camera, 30 mm | 78 |
| S19 | …the man's remains… | The skeleton, clean cream bone, standing wedged between the wall and where the cooler stood | 35 mm push-in | 117 |
| S20 | …wedged behind it | Wider: the skeleton in the narrow strip by the wall, with the contractors at the moved unit looking at it | 26 mm pull-out | 117 |

Phase 1 total: 2496 frames (41.6 s of clips) for a reference of about 34 s.

## Logo: DA KRAS FILMS
- **One placement:** the white logo printed on ConA's orange back, the same idea as the reference's shirt. It's a decal shrink-wrapped to the top and skinned to the rig, so it never floats.
- It reads front-on in S16 and S17 (and partly in S15).
- **Never on:** the cooler (the story's key prop), a face, the 2009 victim shots, or the skeleton shots (S19 is framed on the skeleton; the logo is not on screen there).

## Risky shots: the simplest safe staging used
| Risk (brief or reference) | Staging |
|---|---|
| Reference: head-first fall, the camera inside the wall | He steps back off the rear edge and drops **feet-first**. Every camera is in the open room or above the gap (ceiling raised to 4.6 m); none is inside a wall or cooler. |
| Reference: upside-down body pressed face-first into the floor or wall | He is **upright**, wedged with his chest toward the cooler back and his face turned **up** to the camera. Arms reach up, hands open, with no hand contact on the wall or coils. |
| Skeleton reveal | A clean, cream, non-gory model, upright, revealed by the cooler sliding away. No clothes, no remains texture, no close-up of the skull. |
| Hand contacts | Only S16/S17: palms flat on a flat enamel side panel, placed 14 mm off the surface (checked with `body_prop_cross`). No grips or held props anywhere. |
| Brands | Generic coloured bottles, cans and cartons, a blank blue header, unbranded cardboard. No text anywhere except our logo. |

## Phase 2
Run `transcribe.py` on the VO. Write `timing.json` `{"S01": [in, out], …}` from the word frames. Then `bash scripts/build_all.sh timing.json` lays the clips on the VO without stretching (tails are trimmed). After that, run the checks and preview, and watch every page.
