# NeverBathed: plan (Phase 1, checkpoint P1)

ConnectB31. Branch `claude/connectB31-never-bathed`. 1080×1920, 60 fps, Cycles CPU, hard cuts, shots of 1.5–2.5 s.
Reference: `briefs/batch2/B31_NeverBathed_reference_1fps.jpg` (32 s). It is an **OLD-style** reference (flat sky-blue
backdrop), so we take the story and beat order only and rebuild every scene in a real desert village in our current look.
The shot order follows the reference's line order one to one.

Until the VO arrives, each shot is its own clip at 1×, about 30% longer than its reference slot, laid end to end on a
provisional timeline (`shots_provisional.json`, 2750 frames). In Phase 2 the shot table gets the VO frames and
`03_shots.py` places and **trims** each clip there (no time-stretching).

## Cast (generic, no real likeness)
MPFB2 rigs re-used from our EscapeArtist_v010 package, re-dressed (`scripts/01_chars.py`):
- **AmouY**, the hermit young: dark hair, short dark beard (hair curves), olive work tunic-overall, dark shoes, lightly dusty skin.
- **AmouO**, the hermit old: same outfit and colours (continuity), grey hair, long grey beard (hair curves on the head
  bone, mouth kept clear), sun-darkened skin with stylised soot-brown patches (clean matte, no grime detail).
- **V1** villager: blue shirt and trousers. **V2** villager: brick-red outfit, white skullcap.

All four: eye fix (EnhancedEye cornea → transparent mix), camera-only catchlight per shot, elbow IK limit opened
(−40°…100°), `hand_poses` wrist/finger limits, relaxed hands. Clothes are all non-skin colours.

## Sets (`scripts/02_sets.py`, one scene, areas 200 m apart; each shot has its own camera bound by a marker)
- **V Village lane** (origin): two rows of mud-brick houses (plaster, protruding roof beams, parapets, blue plank doors,
  closed wooden shutters: no black window voids), a back row and a watch tower on the skyline, clay pots, firewood,
  a bench, a stone water trough, stacked wooden crates (**logo**). The hermit's house has an open door with a lit
  interior (floor, rug, pot). The bath courtyard at the lane's end: a tin tub with soapy water, a wooden bucket.
- **D Desert edge** (x=+200): sand dunes, rocks, dry shrubs (hair-curve twigs), the village skyline 40 m away; his
  shallow body-length pit with the dug-out mound and a planted shovel, a folded blanket as a pillow; campfire with
  keyed-noise flame flicker, a meat lump on a spit over two forked sticks; a seat rock; a flat rock with dried dung cakes.
- **R Dirt road** (x=−200): a dusty track with two tyre ruts, roadside posts, a dead hare lying on the verge (no blood).
- Day light: sun + Nishita-type sky (clear blue). Dusk state keyed for beat 11 only (low warm sun).

## Shot table (reference second → our shot); provisional frames in `shots_provisional.json`
| # | Ref s | Line | Shot: who and what they physically do | Camera |
|---|---|---|---|---|
| 1a | 0–1.5 | He thought taking a bath | Young hermit at the stone trough leans in; his left hand reaches down, index finger pointing, and stops ~5 cm above the water. Right hand on his thigh. | 28 mm, front-left 3/4 from past the trough end, low, slow push |
| 1b | 1.5–3 | would make him sick | He pulls back, straightens and turns away from the water shaking his head, frowning (mouth closed). | 40 mm MCU front, slight push |
| 2a | 3–4.5 | So for over | Young hermit portrait in the lane, breathing, slow head turn. | 40 mm, slow orbit right→left |
| 2b | 4.5–6 | 60 years | **Age cut**: the old hermit in the same place and framing; the orbit continues. | same orbit continued |
| 2c | 6–7.5 | he refused to wash | Old hermit at the same trough: looks at the water, turns his body and head away, left palm raised "no" at chest height, lowers it. | 34 mm, front 3/4, slight drift |
| 3a | 7.5–9 | Saying the dirt | In the lane he flexes both arms like a strongman (fists at shoulder height, below the head), pumping twice, chest out. | 28 mm, low, push-in |
| 3b | 9–10 | kept him healthy | Villager V1 by the shop crates watches him and shakes his head. **Logo** on the top crate. | 30 mm, slow lateral |
| 4a | 10–11 | Instead he left his home | He walks out through the open door of his house into the lane, arms swinging. | 28 mm, from the lane, pan with him |
| 4b | 11–12 | (left his home) | He walks down the lane toward the village edge, toward camera 3/4. | 26 mm, tracking back |
| 5a | 12–13 | and dug | At the desert edge he kneels at the pit's rim and scoops loose soil out with both cupped hands. | 28 mm, low across the pit, face visible |
| 5b | 13–14.5 | a shallow hole | He lies on his back in the shallow pit, head on the blanket, hands on his belly, breathing; head turns. | 26 mm high 3/4, crane up |
| 6a | 14.5–15.5 | He ate only roadkill | Dirt road: he kneels by a dead hare on the verge, hands on thighs, leaning in to study it. No hand contact. | 30 mm, low front 3/4 |
| 6b | 15.5–16.5 | (roadkill) | At his campfire a lump of meat roasts on a spit (no hands); seated on the rock he leans in, sniffs, nods. | 32 mm, across the fire |
| 7a | 16.5–17.5 | and smoked animal poop | Insert: dried dung cakes on a flat rock beside his pipe; a wisp of smoke rises from the bowl. No hands. | 40 mm, f/11, slow push |
| 7b | 17.5–19 | out of a pipe | Seated, he holds the pipe bowl in his right fingers, stem tip at his lips (not in the mouth); lowers it and exhales smoke, raises it again. | 40 mm MCU front 3/4 |
| 8a | 19–21 | burning his hair | Seated, he holds a smouldering twig (tiny flame at the far tip) in his right fingers to the very ends of his beard at chest height: a small singe and smoke. No flame near the face. | 38 mm MCU |
| 8b | 21–22 | over a fire | Wide: the hermit at his fire by the pit; smoke drifting off the beard ends. | 24 mm wide |
| 9a | 22–24 | he became the dirtiest man | Hero portrait in the lane, low angle; four flies circle above his head (above the hair, never near the lens). | 30 mm, low push-in |
| 9b | 24–25.5 | in the world | Orbit from front to his left side (face stays 3/4), revealing the lane. | 26 mm orbit |
| 10a | 25.5–27 | Until someone finally convinced him | V1 talks to him and points an open hand toward the tub; the hermit looks at it and gives a reluctant nod. | 30 mm two-shot |
| 10b | 27–29 | to take a bath | He sits in the tin tub, water to the chest, hands on his knees; V1 stands behind with both hands resting on his shoulders, rubbing gently; V2 stands by the tub. | 30 mm, front 3/4 high |
| 11a | 29–30.5 | And he died | **Off-screen**: dusk, the empty pit, his pipe resting on the rim, the shovel in the mound. | 28 mm, slow push |
| 11b | 30.5–32 | shortly after | Dusk wide: V1 and V2 stand quietly beyond the empty pit, heads bowed, hands relaxed. Slow pull back. | 30 mm, pull back |

## DA KRAS FILMS logo
- **3b**: white logo decal on the face of the top wooden crate by the shop door, facing the camera (~24°), ~23% of the
  frame width, on screen the whole shot (~1.7 s), f/8. (Also visible small in 3a/4b.)
- No second placement: every later beat is either a key prop (pipe, tub) or the sombre ending.

## Risky shots and their simple staging
1. **Pipe at the lips (7b).** The pipe is placed with its stem tip ~1 cm in front of the lips (on the moustache), then
   gripped at the bowl by the right hand (`grip_object`, Child Of the wrist); only the hand is keyed afterwards. It never
   goes into the mouth and stays below the hair line. If the grip is not clean after one retry: frame 7b as the pipe
   resting in the hand at chest height with smoke from the mouth.
2. **Burning hair (8a/8b).** No flame on the face: a 7 cm flame at the far end of a 42 cm twig touches only the
   lowest beard ends at chest height; smoke puffs and a small singe. The twig is pinched in the right hand.
3. **Flies (9a/9b).** Four tiny flies orbit 15–30 cm above the head; nothing near the lens.
4. **Bath (10b).** Hands rest ON the shoulders (palm contact keyed from the shoulder bone each frame), arms run outside
   the hermit's body; he sits on the tub floor, water to the chest hides the legs.
5. **Death (11a/11b).** Off-screen: the empty pit at dusk, then the villagers standing quietly. No body, no grave close-up.
6. **Trough (1a/2c).** The reaching hand stops above the water inside the trough; the other hand rests on the thigh.
7. **Door (4a).** The door leaf opens inward along the interior wall; the walk path clears it by ~0.5 m.
8. **Seated on the rock (6b–8b).** Flat-topped seat rock; pelvis 3 cm above it.

## Look
Bright clean 3D animation (`STYLE_ANIMATED.md`): AgX Punchy, exposure −0.9 (the sand is very bright), sky-blue day,
saturated clothing, stylised clean "dirt" on the hermit only. f/8 everywhere, f/11 on the 7a insert.

## Phase 2 notes
Shot table → VO frames (`1 + round(s × 60)`), clips trimmed at their end. Several clips can trim heavily (most beats are
~1–1.5 s in the reference); none needs extending.
