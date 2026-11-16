# B19 ClosetBathroom: Phase 1 plan

**Chat:** ConnectB19 · **Branch:** `claude/connectB19-closet-bathroom` · **Format:** 1080×1920, 60 fps, Cycles, hard cuts (one camera per shot, bound to timeline markers).

**Timing is provisional.** The shots follow the reference film's pacing, about 1 s per reference frame: frames 1–2406, 40 s against the reference's 35 s, so every clip has handles.

**How Phase 2 retimes without stretching:**
- Every action in `scripts/03_shots.py` is written as `F(shot, seconds)` from its shot's start frame.
- Every action ends in a live idle (breath, head turn or camera push) that runs to the shot's last frame.
- In Phase 2 only the `SHOTS` table changes, to the VO word frames (`1 + round(s × 60)`), and the script is re-run. Nothing is time-stretched.
- The shot list is in `shots_provisional.json`.

**Build (fully scripted):**

| Step | Script | Run with |
|---|---|---|
| Characters | `01_chars.py` | Blender |
| Sets | `02_sets.py` | Blender |
| Brain-scan and memory-closet graphics | `02b_graphics.py` | Blender |
| Memory-cloud image | `02c_cloud.py` | system Python with PIL |
| Animation and cameras | `03_shots.py` | Blender |
| Checks | `check_frames.py`, `bpc_range.py` | Blender |

## Cast
Generic MPFB/MakeHuman (CC0) bodies, reused from earlier studio packages because the MakeHuman asset server is unreachable. Each one is recoloured, and its hand gloves are switched back to skin.

| Character | Look | Source body |
|---|---|---|
| **Tom**, the man | light-blue T-shirt, dark jeans, red shoes, brown hair | BelugaRescue `SpecF` |
| **Ray**, roommate 1 | off-white T-shirt, jeans, light-brown hair | EarInArm `Surgeon` |
| **Ken**, roommate 2 | mustard-yellow shirt, jeans, ginger hair | BellyFat `ShopperA` |
| **Doc** | white blouse, navy skirt, dark ponytail | FanCancer `Doctor` |

Every character has:
- the eye fix (`scripts/eye_fix.py`, applied to every EnhancedEye group)
- a ≤ 8 W face fill riding with each shot's camera, for the catchlight
- the elbow IK limit opened to −40°
- STYLE hand limits and the `relaxed` hand preset

Clothes are solid, non-skin colours.

## Sets
- **Hall and living room:**
  - light-blue walls, wood floor and white baseboards
  - the closet door (wood casing, lever handles) and a second closed door
  - a sunny window, sofa, rug, lamp, plant, framed picture and ceiling lights
- **Small room behind the door** (1.6 × 1.9 m), in three dressings switched per shot:
  - `DRESS_Bath`: tiles, toilet, pedestal sink, mirror, picture, towel, paper holder, bin and mat
  - `DRESS_Closet`: rail of hanging shirts, shelf with folded clothes, a box carrying the **logo**, and a laundry basket
  - `DRESS_Prank`: the closet half-converted, with a new toilet, the toilet's cardboard box carrying the **logo**, a bucket, and the old shelf
- **Clinic:**
  - desk, monitor, two chairs, a white cabinet row and an exam bed
  - a wall clock and first-aid box, with no text
- **Graphics:**
  - `assets/brain_scan.png`: a glowing blue head profile and brain with an orange tumour, on a dark navy screen
  - `assets/memory_cloud.png`: the closet render inside a thought-cloud
- Real models are CC-BY (credits in `assets/credits.json`): toilet, sink, toilet paper, folded clothes, sofa, desk, monitor (brand texture replaced with plain black), two chairs, clock, first-aid box and brain.

## Beats and shots (reference order and framing)

| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| He opened his closet (0–1) | S01 | 1–96 | Back view. Tom walks up and raises his right hand toward the door (no contact, see risky shots). The door swings open and he steps into the doorway. | Behind-left, 1.4 m, slow push-in. 26 mm. |
| but instead (1–2) | S02 | 97–162 | Over the shoulder in the doorway: he leans in and looks left and right. The bathroom shows. | Behind-right over the shoulder, push-in. 24 mm. |
| discovered a bathroom (2–4) | S03 | 163–276 | The bathroom alone: sink, toilet, mirror, picture, towel. | Push from the hall to 1.1 m before the door plane. 26 mm. |
| Confused (4–5) | S04 | 277–342 | Close-up: Tom turns his head and leans back, with the bathroom behind him. | 50 mm, front three-quarter, push-in. |
| he asked … what happened (5–7) | S05 | 343–438 | Tom faces the living room, both palms up ("what happened?"). | Medium front from the living room. 30 mm. |
| to the closet (7–8) | S06 | 439–522 | His right arm sweeps back toward the doorway with an open palm, head turning to it. | Front-left medium. 28 mm. |
| They looked at him (8–9) | S07 | 523–612 | Living room: Ray shrugs with palms up and a head tilt. Ken shifts his weight and tilts his head, standing apart (no merged heads). | From Tom's side. 30 mm. |
| like he was joking (9–10) | S08 | 613–690 | Ray laughs it off: head back, right hand waves. | Medium close on Ray. 40 mm. |
| insisting … always been a bathroom (10–12) | S09 | 691–822 | Two-shot at the doorway. Both are turned three-quarter to camera so the faces read. Ray gestures with an open palm toward the bathroom. | Wide from the living room, push-in. 28 mm. |
| He assumed (12–13) | S10 | 823–894 | Close-up: Tom drops his chin and his eyes slide to the side, suspicious. | 50 mm. |
| they had pulled off an elaborate prank (13–15) | S11 | 895–1014 | Imagined: the closet half-converted. Ray stands by the new toilet and presents it with an open palm. Ken grins behind. **Logo** on the toilet's cardboard box, fully in frame. | From the hall through the doorway. 24 mm. |
| while he was gone (15–16) | S12 | 1015–1112 | Ray and Ken turn to each other and nod. | Second angle, push-in. 30 mm. |
| But as days passed (16–18) | S13 | 1113–1236 | Tom walks from the living room back to the doorway (arm swing) and stops, looking in. | Side tracking. 28 mm. |
| his confusion turned to panic (18–20) | S14 | 1237–1356 | He turns from the doorway, puts both hands to the sides of his head and steps back. | Front medium, push-in. 30 mm. |
| couldn't even remember what the closet looked like (20–23) | S15 | 1357–1566 | Close-up: his face in the lower third, looking up at a thought-cloud above his head that shows the closet. The cloud breaks into tiles that scatter and vanish. | Low front, slow push-in. 26 mm. |
| he was losing his mind (23–24) | S16 | 1567–1656 | Close-up: slow head shake and a breath. | 50 mm. |
| the doctor (24–26) | S17 | 1657–1776 | Clinic: Tom sits on the patient chair, hands on his thighs, his left knee bouncing nervously. Clock and first-aid box behind him. | Front three-quarter from the doctor's side, push-in. 30 mm. |
| After some tests, they found (26–28) | S18 | 1777–1926 | The doctor, seated, turns to the monitor and points at the scan (fingertip about 5 cm off the screen). | Wide side angle on desk, monitor and doctor. 28 mm. |
| a brain tumour … memory loss and hallucinations (28–32) | S19 | 1927–2166 | The scan fills the frame: blue head and brain, orange tumour. | Push-in on the monitor (0.62 → 0.36 m). 35 mm. |
| it had always (32–33) | S20 | 2167–2286 | Tom in the doorway looking in. His shoulders settle and he nods. | Behind-right, push-in. 26 mm. |
| been a bathroom (33–35) | S21 | 2287–2406 | The bathroom alone: closing image. | Push-in to 1.1 m. 26 mm. |

**Logo (DA KRAS FILMS, dark version):**
- **Main placement, S11–S12:** front of the toilet's cardboard box, flat to camera. In S11 it is fully in frame for 2 s, at about 25% of the frame width.
- **Secondary:** the closet shelf box carries it too. It is visible only small inside the S15 memory cloud, so it does not count as a full placement.
- Neither is in a sad beat.

## Risky shots: the staging used
- **Door opening, hand on the handle (S01):** a palm-push contact was tried twice. The wrist limit tipped the fingers into the leaf (`body_prop_cross` flagged it), so per LESSONS §2.15 it was re-staged simpler:
  - Tom raises his right hand toward the door, in front of his chest. From the behind-left camera his own back hides it, as in the reference.
  - The door swings away and nothing touches the leaf.
  - **Result: 0 crossings.**
- **Roommates' faces readable:**
  - S07: Ray and Ken stand apart, both facing camera three-quarter.
  - S08: close on Ray.
  - S09: both turned three-quarter to camera.
  - S11 and S12: both face the camera (no backs, no contact with the toilet).
- **Brain scan:** a clean emissive graphic on the monitor. The monitor's brand texture is replaced with plain black.
- **"PRANK" signs:** none. The prank is shown by staging (toilet, box, bucket), with no text anywhere.
- **Hands on head (S14):** the palms are placed 2 cm off the head sides from the evaluated head bone, with the elbows out. Watch this at P1.

## Known items for the director
- No facial expression rigs: these bodies have no face bones. The acting is head, neck, spine and arms, with neutral faces. Mouths are closed and eyes clear.
- The doctor is female (the white-blouse body). There is no mask and no stethoscope, to avoid worn-item risk.
- Raw `pipeline/body_prop_cross.py` flags Tom's thighs against the patient chair (S17). These were checked: all are MPFB **HelperGeometry** vertices, which are masked at render time.
  - `scripts/body_prop_cross_nohelper.py` (the same script, skipping helper and joint-cube vertices) reports **0 crossings** for the whole film.
