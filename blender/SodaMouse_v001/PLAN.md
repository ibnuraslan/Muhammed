# B10 SodaMouse: Phase 1 plan (Connect B10)

**Reference:** `briefs/batch2/B10_SodaMouse_reference_1fps.jpg` (old style: blue-grid studio). We match its shot order, subjects and pacing, built on real sets (kitchen and lab) in our bright animated look.

**Format:** 1080×1920, 60 fps, Cycles, hard cuts (one camera per shot, switched by timeline markers).
**Characters:**
- **SodaMan**: MPFB, light-blue short-sleeve shirt with the DA KRAS FILMS logo on the chest, jeans.
- **Scientist**: MPFB, white lab coat, pale-blue shirt, red tie, latex gloves.

Both have:
- the eye fix
- hand limits
- elbow IK limit opened to −40°
- a ≤2 W camera catchlight on face shots

**Props:**
- a generic green can (no brand, no text)
- a plate with a green puddle
- a dead mouse lying on its side
- a 1 L beaker with green soda
- a steel spatula and a steel tray
- a green jelly lump

**Clips:** each shot is its own 1× clip about 30% longer than the expected beat (`03_anim.py`, `CLIP` table). Phase 2 lays them on the VO frames and trims only the tails. No time-stretching.

| Shot | Beat (reference words) | Set | Who and what they physically do | Camera | Clip len (f) |
|---|---|---|---|---|---|
| S01 | A man claimed he found a… | Kitchen | Man stands at the table and lifts the can (right hand, in the fingers) to his lips; he drinks, his head tilting back as the can tilts. Left arm relaxed. | Side ¾ MCU from his left, slow push-in, 55 mm f/9 | 156 |
| S02 | …dead mouse inside a can… | Kitchen | Macro of the can top on the table: a pink tail tip curls out of the opening. No hands. | Top-down macro push to the opening, 70 mm f/11 | 117 |
| S03 | …of [soda] | Kitchen | Hero can in the low foreground; the man stands behind and looks down at it (arms relaxed). | Low table-level wide, slow lateral move, 30 mm f/8 | 117 |
| S04 | he was drinking | Kitchen | Mouse on the plate in green soda. The man lowers the can, looks, recoils (steps back, head turns away, free hand up open in disgust). | Front medium-wide, push, 32 mm | 117 |
| S05 | So he sued… | Kitchen | Man leans in and points at the mouse on the plate with his right index finger, talking. | Front ¾ medium, push, 35 mm | 117 |
| S06 | …the parent company | Kitchen | CU: dead mouse on its side in the green puddle on the white plate. | High ¾ macro push-in, 60 mm f/11 | 117 |
| S07 | [Company] argued… | Lab | Scientist behind the steel table raises his right index finger beside his shoulder as he speaks; beaker and can on the table. | MCU front ¾ push, 42 mm | 117 |
| S08 | …that [soda]'s highly acidic formula… | Lab | Scientist pours the can (right hand) into the beaker; green stream; the level rises; bubbles. | Medium (face in frame), push, 35 mm | 156 |
| S09 | …would actually… | Lab | Scientist tilts a steel spatula over the beaker; the mouse slides off the blade and drops into the soda. | Medium from his right, push, 35 mm | 117 |
| S10 | …dissolve a mouse body into a… | Lab | Side macro of the beaker: the mouse sinks among fizz, shrinks and turns into a green jelly lump. No gore. | Macro push, 70 mm f/11 | 156 |
| S11 | …"jelly-like" substance… | Lab | Scientist tips the beaker; the jelly lump slides out onto the steel tray and wobbles. | Medium ¾, push, 40 mm | 156 |
| S12 | …before anyone could notice it in the can | Lab | CU: jelly lump wobbling on the tray, can beside it. | Low ¾ macro push, 60 mm f/11 | 156 |
| S13 | This odd defense left consumers worrying… | Kitchen | Man holds the can at chest height, turns it and studies it, worried (head tilt, eyes on the can). | MCU push, 55 mm | 156 |
| S14 | …what the soda really does… | Kitchen | Man sets the can down and slides it away from himself, lets go, straightens up. | Side ¾ medium, 38 mm | 117 |
| S15 | …to the human body | Kitchen | Man looks down at his belly, left hand flat on his stomach, right arm relaxed. Logo front-on. | Front medium, push, 32 mm | 156 |
| S16 | if it can liquefy a mouse | Kitchen | Final CU: his eyes go to the can on the table and back; slight worried breath (mouth barely parted, no teeth). | CU push, 60 mm | 156 |

## Logo: DA KRAS FILMS
- **One placement:** the dark logo printed on the man's light-blue shirt chest, the same idea as the reference shirt. It's a decal shrink-wrapped to the shirt and skinned to the rig, so it never floats.
- **Readable front-on (within 30°, at least 15% of frame width, at least 1 s):** S03, S04, S05, S13, S14, S15.
- **Never on:** the can (the story's key prop), a face or skin, or the lab shots.

## Risky shots: the simplest safe staging used
| Risk | Staging |
|---|---|
| Reference: liquid stream poured into the mouth, see-through can with the mouse inside | Normal drinking from a solid can (S01). The mouse is shown as a tail tip at the opening (S02) and then on the plate (S04–S06). No x-ray can. |
| Reference: man spitting the mouse out | Recoil from the plate instead (S04). Nothing comes out of a mouth. |
| Reference: flask held at the man's eye or face | Dropped. No liquid near an eye or face. The worry beat is the can at chest height (S13). |
| Reference: belly dissolving into goo | Dropped. He looks down with a hand flat on his stomach (S15). |
| Mouse dissolving | Clean, non-gory: it shrinks, darkens into the green and becomes a smooth jelly lump. |
| Grips | Can, spatula and beaker are Child Of the wrist bone from the grip frame (`grip_object`, no gap). Every hand has its arm and body in frame. |
| Brands | Generic green can with a zig-zag graphic, no text. No real company named or shown. |

## Director P1 notes (fixed in P1b)
1. Can: opaque printed aluminium (solid green print, diagonal white zig-zags). No band that reads as a liquid level.
2. S10: glass, soda and bubbles cast no shadows, plus a back light and fur sheen. The grey mouse reads as it sinks.
3. S12: the scientist is hidden and the camera is more top-down. No blurred white shape; the jelly has form.
4. Relaxed arms (all characters): elbow bent, hands resting by the front of the thighs.
5. S07: small finger raise close to the chest, palm side-on.
6. Key, fill and top lights lowered about 0.5 stop. Kitchen walls pale sage, lab tiles pale blue.
Answers: no courtroom, one consumer, re-dressed rigs OK.

## Unsure / for the director (P1)
1. **Courtroom:** the brief mentions a courtroom set, but the reference (which the client now wants matched) has no courtroom; it stays in the kitchen for "So he sued". I can add one courtroom shot (the man standing at the plaintiff's table) if wanted.
2. **Consumers (plural):** the reference uses the same man. I kept one man. A second worried consumer is possible in S13 if wanted.
3. **MakeHuman asset server:** it was unreachable (proxy 502), so both characters were re-dressed from MPFB rigs already used in our delivered packages (BellyFat ShopperA, SurgeonBrandsLivers Surgeon1). The faces are generic.
4. **Source file:** `SodaMouse_v001_phase1.blend` (29 MB, packed). It's the source for Phase 2, because the scratch assets used by the scripts don't survive the container.
