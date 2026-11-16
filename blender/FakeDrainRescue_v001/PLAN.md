# B29 FakeDrainRescue: Phase 1 plan

ConnectB29 · branch `claude/connectB29-fake-drain-rescue` · 1080×1920 · 60 fps · Cycles · hard cuts (one camera per shot, bound by timeline markers).

**The timing is provisional.** It follows the reference sheet's order and pacing: 25 shots, frames 1–2640 (44 s). The table is in `shots.json`.
The whole build is scripted (`scripts/00`–`04`), and every shot is a function of its own window:
- Each action runs at 1× for **1.3× its provisional window**. The cut trims it.
- In Phase 2 I only change `shots.json` to the VO word frames (`1 + round(s × 60)`) and rebuild. Nothing is time-stretched.

**Characters:** generic MPFB/MakeHuman CC0 bodies reused from studio packages, each recoloured and re-dressed. All 7 rigs have:
- the eye fix
- a glossy-only catchlight beside every camera
- the elbow IK limit opened (−40°…140°)
- relaxed `hand_poses`

The mother's fringe is lifted above her brows, so both eyes show.

**Story risk (brief):** no child is ever shown falling. The boy appears only in S01, walking beside her before her story, and is never in or near the water. "Fell into the drain" is told by her pointing at the trash.

## Beats and shots

| Beat (ref s) | Shot | Frames (prov.) | Who and what, physically | Camera |
|---|---|---|---|---|
| Her child accidentally fell (0–2) | S01 | 1–120 | Mom (pink blouse, plum trousers) and her small boy (green tee) walk along the coping of a trash-choked storm drain. The boy walks on her inside, 0.45 m from the edge. | High three-quarter over the drain, slow drift back. |
| right into | S02 | 121–210 | Mom stops at the edge, leans, and points down into the trash (point pose, arm down and forward). Her other arm hangs. | Over the drain, looking up at her across the trash. |
| the storm drain | S03 | 211–300 | Top-down wide of the long drain packed with coloured bags, bottles, cans, boxes and tyres. Mom is small at the edge, stepping back. | Top-down crane up. |
| is what she told | S04 | 301–400 | Mom close, pleading: both hands open at chest height, alternating, with a head tilt. | 45 mm front, slow push. |
| the police | S05 | 401–510 | Mom with two officers (olive uniforms, peaked caps) on the drain edge. The officers stand turned toward her in a loose triangle, not a lineup. She gestures toward the drain; one officer nods, the other looks at the drain. | Street side, three-quarter, push-in. |
| So they spent hours | S06 | 511–630 | Two rescuers (hi-vis vests, hard hats) wade waist-deep through the murky water among floating trash, hands sweeping at the surface. | Down the drain from the coping, slow descent. |
| sifting through trash | S07 | 631–735 | Medium: the lead rescuer pushes forward, arms sweeping the surface trash aside. | Low over the water, in front of him. |
| desperately looking | S08 | 736–840 | At the culvert mouth he shines a torch beam into the pipe. His right fist is on the far side of his body, so no torch model is shown (see risks). | Front three-quarter, pipe beside him, push and arc. |
| for any sign of life | S09 | 841–930 | Into the dark culvert: the torch beam sweeps over trash jammed inside the pipe. | Beside him, looking into the pipe. |
| But there wasn't | S10 | 931–1030 | He turns, lowers the torch and shakes his head. | Close, front. |
| anyone inside | S11 | 1031–1140 | **Clean state:** a top view of the cleared drain (clear blue water) with rows of filled bags on the edge. The rescuers stand at the edge looking down. | Top-down, rising. |
| You see the woman | S12 | 1141–1250 | Back in the dirty state: Mom walks along the trash, looking down at it, annoyed. | Front, tracking back. |
| couldn't stand | S13 | 1251–1340 | Mom close, low angle: she frowns and shakes her head. Sky behind. | Low front close. |
| the trash clogging up | S14 | 1341–1450 | Trash jammed in front of and inside the culvert. No person. | Push-in over the water. |
| And even though | S15 | 1451–1550 | Office: a clerk sits back from a metal desk with a tall pile of complaint forms. His knees are clear of the desk and he leans forward with his palms flat on the desk top, looking around, unbothered. | Front, push-in. |
| people already made complaints | S16 | 1551–1670 | The pile of forms. Each form is **text-free**: a photo of trash, empty field boxes and a red stamp ring. The clerk is behind it. | Over the desk, push down. |
| nothing changed | S17 | 1671–1780 | More bags and bottles float out of the culvert and pile up (keyed drift plus a bob noise; water carries them). | High side, slow push. |
| So she made up | S18 | 1781–1880 | Mom close: her head lifts from looking down. The idea lands, and she looks up and toward camera. | 45 mm front. |
| this fake | S19 | 1881–1960 | Her phone in her fingers below her face, the call screen readable (pictograms only: avatar, keypad, green and red buttons). | Close on the phone, along the screen normal. |
| emergency to tell | S20 | 1961–2070 | Mom holds the phone at chest height and talks into it, looking at it. | Medium front. |
| the police | S21 | 2071–2160 | Same, from the side: she glances toward the drain, phone still in hand. | Side three-quarter. |
| just a few hours of searching | S22 | 2161–2280 | Clean state: a rescuer walks the sidewalk past two long rows of filled bags; the other stands at the edge. | Front low, tracking. |
| of searching | S23 | 2281–2400 | A green garbage truck with the **DA KRAS FILMS** logo parked by the cleared drain. | Street level, near flat-on to the logo panel, dolly along it. |
| the drain was | S24 | 2401–2520 | Wide: the long clean drain, blue water, bags lined on both edges, rescuers at the edge. | High from the culvert end, drift. |
| left totally clean | S25 | 2521–2640 | Top-down crane up over the clean drain. The truck pulls away down the street. | Top-down rise. |

## DA KRAS FILMS logo
- **One placement:** the white logo on the green refuse box of the garbage truck (S23, 1.6 m wide on the flat side panel, about 20° from flat-on, f/∞ with no DOF).
- The truck also appears in S22, S24 and S25.
- It is the neutral, happy end of the story. There is no logo in the fake-emergency or search beats.

## Risky shots and the simplest safe staging
- **No child falling:** the boy only walks (S01). The fall exists only in her pointing (S02) and the VO.
- **Rescuers' hands in the trash:**
  - Their hands sweep just above the water surface, with no grip on trash.
  - Wading corridors are cleared of floating trash (0.75 m radius), so no body passes through a bag.
  - `body_prop_cross` checks every bag near the corridors.
- **Phone below her face:**
  - Hold-flat-object pose, Child Of `wrist.R`.
  - Held at chest height, never at the ear, so no hand meets the hair or face.
  - The screen is pictograms only.
- **Torch:** the first P1 build put a torch model in a wrap grip, but `body_prop_cross` found two fingers through it (S08). Following LESSONS §2.15 I dropped the model. The beam is a spot light held by Child Of `wrist.R`, in a fist on the side away from the camera. If you want the torch visible, I'll re-grip it with `grip_object` in Phase 2.
- **Complaint forms:** no text, only a photo, empty boxes and a stamp ring.
- **Office sitting:**
  - The clerk's palms rest flat on the desk top.
  - His feet are on the floor in the desk's knee space.
  - He sits on a monobloc chair (checked against the desk and chair).
- **Lens clearance:** every camera moves through open air or above the water. S14 and S17 were raised clear of the near bags.

## P1 checks
- **Sheet:** `review/P1_sheet_3frames_1.jpg` (S01–S13) and `_2.jpg` (S14–S25). Each shows the first, middle and last frame of every shot at 540×960, Cycles 8 spp.
- **`body_prop_cross`:** run per shot, step 3, on that shot's visible rigs and props. The props are:
  - the phone and the torch
  - the desk, chair and top forms
  - both drain walls, the end wall and the pipe
  - the truck
  - every floating bag, bottle or can within 1.3 m of the wading paths
  - the clog and drift trash, and the clean-state bag rows

  Result: `review/body_prop_cross_P1.json`.
