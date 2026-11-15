# B04 LincolnAssassination: plan (Phase 1, before the VO)

Film: 1080×1920, 60 fps, Cycles, hard cuts, one camera object per shot (timeline markers bind them).
Reference: `briefs/batch2/B04_LincolnAssassination_reference_1fps.jpg` (28 s). Client direction (Nov 15): match its
shot order, subjects, framing ideas and pacing. Built in our current bright look (STYLE_ANIMATED), night scenes blue and readable.

Phase-1 timeline: every shot is its own clip, ~30% longer than the reference shot, laid end to end
(frames below). All animation is keyed from event times in `scripts/timing.py`, so Phase 2 only changes that table
to the VO word frames and rebuilds. Nothing is time-stretched.

## Cast (all generic MPFB characters, no real likeness)
| Name in file | Role | Look |
|---|---|---|
| `Gunman` | the gunman | olive-brown suit, dark short hair (moustache dropped: the borrowed prop sat on the jaw), face shown in every beat he acts |
| `President` | the president | black suit, tall black top hat; **only seen from behind/side-behind**, never a face close-up |
| `ActorA`, `ActorB` | actors on stage (background) | woman in a teal dress, man in a grey suit; small in frame, gesturing (comedy scene) |
| `Soldier1..3` | manhunt soldiers | navy uniform suits + caps, each with a torch in the fingers |
| `Horse` | the escape horse | textured saddled horse (rig from our WW1 film), gallop cycle |

## Shots (Phase-1 frames; reference second in brackets)
| # | Beat (ref VO idea) | Shot / camera | Who and what they physically do | Frames P1 |
|---|---|---|---|---|
| S01 | pulls out a small gun and aims it (0–2.5 s) | Over-the-shoulder, low, behind the gunman's right arm; the gun hand is in the lower third (not filling the frame), the president's top hat centre, stage and actors beyond. Slow push-in. | Gunman's right arm rises from his side, pistol already in the fingers (wrap grip, Child Of hand), and levels at the back of the top hat. President sits still, watching the play, a small breath/head bob. | 1–198 |
| S02 | ...the back of his head (2.5–4 s) | Side medium of the gunman in profile from the box's side wall: his face, arm extended, president seated in front. f/8. | Gunman holds aim, eyes narrow, tiny breath. | 199–318 |
| S03 | waits for a loud moment in the play (4–6 s) | Low angle from behind the armchair, gun barrel in upper left about 40 cm behind the hat, actors on stage gesture big (laugh line). | ActorA throws her arms open, ActorB laughs and leans back; president's head tilts with a laugh. Gun holds steady. | 319–474 |
| S04 | (tension) (6–7 s) | Close-up of the gunman's face, 3/4 front, rack-free f/8. | Jaw sets, slight lean forward. | 475–552 |
| S05 | he pulled the trigger (7–8.5 s) | Close on gun and hat from the side, both sharp. | Finger squeeze (hand pose holds, gun kicks 6° up), stylised muzzle flash + white smoke puff. **Cut on the flash** (no victim reaction shown). | 553–654 |
| S06 | after firing (8.5–10 s) | Medium from the box doorway: smoke hangs, gunman turns to the rail. President out of frame. | Gunman lowers the gun to his side, turns and steps to the rail. | 655–750 |
| S07 | he jumped (10–12 s) | Low angle from the stage looking up at the box (like the reference). | Gunman is already standing on the wide box ledge (climb hidden by the cut), crouches, springs off. | 751–906 |
| S08 | to the stage, breaking his leg (12–14 s) | Wide-medium on the stage at landing height, side-front. | Falls ~2.4 m, lands on both feet, left knee buckles, he drops to one knee, one hand on the floor beside him (palm flat on the boards). | 907–1050 |
| S09 | as he landed (14–15 s) | Close-up of the left lower leg and shoe on the boards, f/8. | Stylised small red crack flash on the shin over the trouser (clean, no wound), leg twitches. | 1051–1128 |
| S10 | despite the injury (15–16 s) | Medium-front, camera backs away as he limps toward it. | Stands, limps (short left step), right hand on his left thigh above the knee, face in pain. | 1129–1248 |
| S11 | escaped the theatre on horseback (16–19 s) | Night street, low camera in the road, horse gallops toward and past camera-left. | Gunman seated in the saddle, feet at the stirrups, hands forward at the reins; horse gallop cycle, hooves planted, no slide. | 1249–1446 |
| S12 | (escape) (19–21 s) | Side tracking shot, camera dollies alongside; DA KRAS FILMS poster on the house wall behind. | Same gallop, rider leans forward. | 1447–1644 |
| S13 | a massive manhunt began (21–23 s) | Street, three soldiers jog toward camera with torches; camera low, slow pull back. Logo on a stack of crates by the door. | Soldiers jog (bent arm swing on the free arm), torch held at chest height in the right fingers, flame above the shoulder but below the head. | 1645–1818 |
| S14 | he hid for 12 days before being found (23–26 s) | Barn interior wide from behind the hay: gunman crouched behind bales, soldiers in the open doorway with torches, stylised fire licking the far wall. | Gunman rises from his crouch, looks to the door; soldiers step in. | 1819–2016 |
| S15 | ...in a barn (26–28 s) | Medium close-up of the gunman, low 3/4 front, flames behind. | He raises both open hands to shoulder height (below the hair line), looks up at the burning roof. Hold ≤2 s, then the film ends on a hard cut. | 2017–2214 |

Phase-1 total 2214 frames (36.9 s); the VO will set the real lengths.

## Logo (DA KRAS FILMS)
- Primary: cream theatre-style poster with the dark logo on a house wall in **S12** (flat to the tracking camera, ≥15% width, ≥1 s, f/8).
- Second: white logo stencilled on the front of a wooden crate stack by a doorway in **S13**.
- Not in the theatre, the shooting or the barn (tragic beats).

## Risky shots: the simplest safe staging
| Risk | Staging |
|---|---|
| Gun in the fingers | `hand_poses.grip_object` wrap grip, pistol Child Of `wrist.R` with zero gap, checked in a close-up still. The gun never moves without the hand. The hand is mid-size in frame (no giant hand); the arm is joined to the visible shoulder. In S05 the finger pose doesn't change (only the gun's recoil follows the hand). |
| Shooting | flash + smoke only; cut on the flash; no wound, no slump shown. |
| Jump and landing | no rail climb on screen (he's on the ledge at the cut). Jump is a clean ballistic arc on the root (no stretch), feet IK; landing contacts checked against the stage floor (no feet through the boards). Knee drop with one palm flat on the floor. |
| Broken leg | stylised red crack flash on the trouser shin only, no blood. |
| Seated on the saddle | rider is Child Of the horse torso bone, pelvis on the saddle seat, legs straddle outside the horse body (body_prop_cross on Horse_body), feet at the stirrups, hands forward at the reins over the withers, elbows bent ~90°. Shots are wide/medium so hand contacts are small. |
| Torches | own simple torch (wood handle + wrapped head + emissive stylised flame), wrap grip in the right fingers, held at chest height. |
| Barn ending | no shooting shown. Gunman surrounded, hands raised open at shoulder height, fire is stylised (emissive flame cards, keyed, no Scene Time). Hard cut to end. |

## Cameras
One camera per shot, `CAM_Sxx`, markers bind them at shot starts. f/8+ for close-ups, f/5.6+ elsewhere. Every camera path checked
at its first and last frame for lens blockers (box rail, chair back, hat brim, hay bales, door frame).

## Phase-1 build notes (as built)
- Box floor is 1.6 m above the stage (ledge top 2.43 m). At 3.6 m the parapet hid the whole stage from the box eye line;
  1.6 m keeps the actors and stage visible behind the top hat (reference framing) and still reads as a real drop.
- Actors stand on the president's sight line just left of the hat in S01/S03 (parlour comedy, big gestures, laugh peaks at the shot).
- President leaves the scene file after S06 (never shown after the shot).
- Gun: real CC-BY flintlock-style pistol scaled to 17 cm, `grip_object` wrap grip (fingers close 0.15/0.63/0.65/0.6),
  Child Of `wrist.R`; the hand is driven from the gun's transform so it never leaves the fingers. Close-ups checked.
- Torches: own torch, wrap grip (0.55/0.55/0.5/0.3), Child Of `wrist.R`, elbow pole keyed so the wrist limit can't twist it.
- S03/S05 cameras are solved to fit muzzle, hand and top hat in frame (`frame_pts`).
