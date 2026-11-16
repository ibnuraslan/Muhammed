# BogBurials: plan (Phase 1, before the VO)

ConnectB33. Branch `claude/connectB33-bog-burials`. 1080×1920, 60 fps, Cycles CPU.
Reference: `briefs/batch2/B33_BogBurials_reference_1fps.jpg` (54 s, 1 frame/s, current style). Client direction (Nov 15): match its
shot order, subjects, framing ideas and pacing, in our current look. Hard cuts, 1–3 s per shot.

Phase 1 timing is provisional: each shot is animated at 1× in its own frame range, about 30% longer than the matching
stretch of the reference (`scripts/shots.py`, 3960 frames ≈ 66 s). In Phase 2 the shot table gets the VO frames and the build
is re-run: every shot keeps its 1× animation and is only trimmed (or extended at 1×), never stretched.

## Build
- `scripts/01_lib.py`: asset library (characters, wolf, props, Poly Haven plants) → `lib.blend`
- `scripts/02_build.py` (+ `shots.py`, `curl_pose.py`, `skel_bind.py`): sets, shots, cameras, markers → the film .blend
- `scripts/shot_frames.py` + `scripts/sheet.py`: first/middle/last frame of every shot → P1 sheet
- `scripts/bpc_range.py`: `pipeline/body_prop_cross.py` on a frame range

## Cast and sets
- **The deceased** (MPFB, re-dressed BellyFat "ShopperC": cream woven garment, leather moccasins). One fixed curled pose for the
  whole film: lying on her right side, knees pulled to the chest, arms tucked with the hands resting on the shins, eyes closed.
  Static baked copies of the same pose are the other burials in the pond and the body in the cross-section.
- **Two burial-party men** (MPFB, re-dressed EscapeArtist "Father" in a hide-brown tunic, BelugaRescue "SpecD" in an ochre tunic).
- **Construction worker** (DrunkTrain "Worker", hi-vis orange coverall, his own approved hard hat).
- **Archaeologist** (FrozenTearsGun "Inventor", khaki field clothes).
- **Wolf** (CC-BY model, grey coat, our quadruped rig). The reference shows a boar; the only boar models were low-poly blocks, so
  a wolf plays "animals". Easy to swap if the director prefers.
- **Skeleton** (CC-BY female skeleton) bound to a copy of the deceased's rig, so it has exactly the same curled pose.
- Sets, far apart in one scene: **bog pond** (x=0: peat floor 0.7 m under clear water, grassy banks, trees), **cross-section**
  (x=100: cut block of mud and peat on the sky-blue explainer gradient), **construction site** (x=200: dried bog, excavator,
  white pickup), **dig** (x=300: main pit with grid strings, 100+ burial pits with orange pin flags).

## Shot table (provisional frames, 60 fps)
| # | Ref s | Ref caption | Who / what physically happens | Camera |
|---|---|---|---|---|
| 01 | 0–2 | "They placed (them) in the water" | Both men stand thigh-deep on either side of the curled body, bent over, palms resting on her upper shoulder and hip, and lower her 22 cm to the peat floor. | Side wide from the bank side, slow push-in. |
| 02 | 2–4 | "with their arms tucked in" | Underwater: the body on the floor, arms tucked, hands on the shins. Men's legs stand in the water behind. | Low underwater, slow lateral drift. |
| 03 | 4–6 | "and knees pulled close" | Underwater close on knees and hands. | Push-in, f/8. |
| 04 | 6–8 | "Then they placed long wooden stakes" | Above water: BurB grips a stake with both hands and pushes it 55 cm down along its axis into the floor; BurA stands behind. | Front 3/4, his face to camera. |
| 05 | 8–10 | "around each of them" | Underwater: three crossed X pairs of stakes over the body; men's legs behind. | Wide, slow drift. |
| 06 | 10–12 | "to pin them to the bottom of the bog" | Low underwater angle under the crossed stakes. | Low, slow slide. |
| 07 | 12–15 | "so the water didn't push them back to the surface" | The body rises 3 cm twice and settles; the stakes hold it. | Looking up past the body to the bright surface. |
| 08 | 15–17 | "which prevented animals" | The wolf walks down the bank to the water's edge. | From the bank, high-ish, slow push. |
| 09 | 17–19 | "from eating them" | The wolf sniffs toward the stakes poking out of the water, then lifts its head and turns away. | Over the water, 42 mm. |
| 10 | 19–22 | "Once the bodies…, a thick layer of dead plants" | Underwater: dead leaves sink and settle; a peat layer rises over the body. | Underwater, slow rise. |
| 11 | 22–25 | "sealed them in like a lid" | Cross-section: the peat lid (with grass on top) drops onto the layer over the body; stakes in section. | Front of the cut, push-in. |
| 12 | 25–27 | "blocking out air" | Glowing light-blue air bubbles sink, bounce off the lid top and drift away. | Front, slightly high. |
| 13 | 27–30 | "and preventing the bodies from decaying" | Close on the intact body in the peat niche. | Slow push to the body. |
| 14 | 30–32 | "But 8,000 years later" | Wide: the dried bog is now a construction site, excavator, white pickup; the worker walks in. (No "8000 YEARS" text.) | High wide, crane down. |
| 15 | 32–34 | "a construction crew" | The worker walks toward camera past the white pickup. **Logo on the pickup's driver door.** | Medium, the door flat-on behind him. |
| 16 | 34–37 | "hit a human skull" | A skull lies in the dug earth; the worker bends over it, looking down at it. | Low near the skull, his face above. |
| 17 | 37–40 | "Archaeologists … uncovered" | The archaeologist kneels at the pit edge beside the curled skeleton, leaning in. | Across the pit, her face to camera. |
| 18 | 40–43 | "168 burials" | Top-down crane-up over the field: 100+ pits with flags, skeletons in them. | Vertical rise 6 m → 19 m. |
| 19 | 43–45 | "so well preserved that their stomachs" | She brushes the soil beside the bones (brush in her right fingers, never touching bone). | Across the pit. |
| 20 | 45–47 | "still held their last meals" | Close on the abdomen: a clump of seeds and plant fibres; the seeds glow warm yellow. | Close from above, f/11. |
| 21 | 47–50 | "their skulls still held their brain" | An opened skull in the next pit (cap lifted): the shrunken brown brain inside. Clean cross-section. | Slow orbit, f/11. |
| 22 | 50–52 | "their bones were still wrapped in burial cloth" | The skeleton under remnants of the woven linen garment (holes, frayed). | 3/4 from above. |
| 23 | 52–54 | "and their bodies kept the curled shape" | Top-down on the curled skeleton, slow rotate. | Overhead. |
| 24 | 54+ | "they were buried in 8,000 years ago" | Hard cut: the woman as she was laid down, same pose, same pit, same framing. | Overhead, slow rotate. |

## Logo (DA KRAS FILMS)
One placement: the white pickup's driver door (dark logo, flat-on, about 30% of the frame width, whole of shot 15).
Never on the bodies, skeletons or in the burial beats.

## Risky shots and their simplest safe staging
- **Placing the body (01):** palms rest on top of her shoulder and hip (contact from above, no hand under or through the body);
  the men's arms stay on their own side of her. Checked with body_prop_cross (hands vs her body, garment and hair).
- **Stakes (04–10):** crossed pairs whose shafts cross 20 cm above her top and whose bases are 0.8 m to either side; none touches her.
  Only one stake moves (04), pushed along its own axis with both hands on it.
- **Underwater (02–07, 10):** clear water with a faint green tint and a transparent surface (no mirror, no murk); sun light
  reaches the floor.
- **Death and remains:** no death on screen, no distress; eyes closed, peaceful. Skeleton and skull are clean cream bone, no gore.
  Brain is a clean cross-section (skull cap lifted), not an x-ray.
- **Brush (19):** brush in the fingers, strokes the soil 10 cm off the bones.
- **No text:** no "8000 YEARS", no arrows, no numbers. Excavator's brand text removed (plain yellow), pickup repainted white.
