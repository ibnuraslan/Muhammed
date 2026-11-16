# MomLiftsCar (B14): plan (checkpoint P1)

ConnectB14. Branch `claude/connectB14-mom-lifts-car`. 1080×1920, 60 fps, Cycles CPU, hard cuts (one camera object per
shot, bound with timeline markers).
Reference: `briefs/batch2/B14_MomLiftsCar_reference_1fps.jpg` (30 s, OLD style, flat sky-blue backdrop). Per the brief we
keep its shot order, subjects and framing ideas, and rebuild every scene with real sets in our current look.
The VO is not in yet. Each beat is animated at 1× as its own clip, about 30% longer than the reference beat, in its own
frame window below. In Phase 2 each clip is shifted (never stretched) so it starts on its VO word, then trimmed.

## Phase-1 timeline (clip windows; replaced by VO frames in Phase 2)
| Beat | Clip window (frames) | Ref. time | Story line |
|---|---|---|---|
| B1 the lift | 1–600 (10.0 s) | 0–8 s | In 1964 a mother lifted a car that had fallen on her son, all by herself |
| B2 hysterical strength / adrenaline | 601–1200 (10.0 s) | 8–17 s | This is called hysterical strength… the body releases large amounts of adrenaline in response to extreme stress |
| B3 blood flow, oxygen, energy | 1201–1680 (8.0 s) | 17–23 s | This rapidly increases blood flow to your muscles, giving them more oxygen and energy |
| B4 brief impossible strength | 1681–2200 (8.7 s) | 23–30 s | And it allows brief moments of incredible strength that are usually impossible under normal conditions |

## Sets (one scene, sets far apart)
- **SetDrive** (x = 0): 1960s suburban driveway. Concrete driveway with joints, lawn, pale-yellow house with shutters and a
  red door, a garage at the end of the drive, white picket fence, bushes and trees, sidewalk, street, three neighbour houses
  across the street. **The car**: a 1953 sedan model (CC-BY), repainted the reference's pale mint green, scaled 0.82. Its
  trunk chevron badge is painted over and the number plate is covered with a blank plate (no text, no brand). A toppled red
  scissor jack lies beside the rear-left wheel (why the car fell). The car is lifted by rotating it about its front-axle line
  (rear rises 0.26 m, 3.3°), with a small strain tremble while held.
- **SetBody** (x = 40, raised to z = 100 so only sky is behind it): clean colour-coded anatomy on the sky gradient. Kidneys
  with aorta and vena cava (CC-BY model) plus our yellow-orange adrenal glands on top; amber adrenaline droplets; a muscle bed
  with branching arteries shown as a clean open cross-section (red walls, dark-red lumen) and red blood cells (biconcave discs)
  plus green oxygen dots flowing inside; a spindle muscle made of fibre bundles with cream tendons.
- **SetPark** (x = 80): park lawn, path, a fallen tree trunk with branch stubs (Poly Haven CC0 bark), bench, hedges, trees.

## Shot list (1–2.5 s each; every shot has a moving subject and a slow camera move)
| Shot (frames) | Beat | Who / what, physical action | Camera | Risk → safe staging |
|---|---|---|---|---|
| 1a (1–110) | B1 | High top-down over the car's rear (the reference's opening): Mom (red polka-dot blouse, jeans, ponytail) crouches at the rear bumper, hands under it, and starts to heave; the car's rear begins to rise | Top-down from above the trunk, slow descent | Hands under the bumper lip (body_prop_cross on the car) |
| 1b (111–260) | B1 | Side wide (reference 1–3 s): she drives up out of the squat, the car's rear rises; the son lies on his back beside the car, his legs pinned under the rear overhang | From the left side, slow dolly | Car underside clears his legs by ≥ 1 cm at rest (measured), then rises 0.26 m; no crossing |
| 1c (261–380) | B1 | Low 3/4 rear-left by the rear wheel (reference 3 s): the car held up, the son on his back beside it, legs under the car | Low, near the ground, slow push | Camera ≥ 1.4 m from the bumper; jack visible as the cause |
| 1d (381–470) | B1 | Mom's face straining (reference 4 s): she looks down at her son, breathing hard, hands on the bumper below frame edge | From above the trunk lid (outside the car), f/8 | Face fill: sun + catchlight only; mouth closed |
| 1e (471–600) | B1 | Low angle from the ground at the rear-left corner (reference 5–8 s): the son's face right at the car's side edge, the raised car body above him, he turns his head toward his mother | Ground level, slow push-in | Face clear of the car body; no distress close-up (he looks up, calm) |
| 2a (601–780) | B2 | Mom in side profile holding the car up, straining, small tremble (reference 8–12 s) | Side medium from the left, slow push | Hands under the bumper lip |
| 2b (781–1000) | B2 | Kidneys and their adrenal glands; the glands pulse and glow and amber adrenaline droplets stream out (reference 12–16 s "releases large amounts") | Front, push-in | Clean anatomy, no x-ray of a person |
| 2c (1001–1200) | B2 | Closer on one adrenal gland releasing a burst of droplets | Slow orbit, f/11 | Droplets keyed (no Scene Time) |
| 3a (1201–1440) | B3 | Branching arteries over muscle, cut open: red cells and green oxygen dots rush along the trunk and split into both branches (reference 17–21 s) | From above, gliding forward over the split, f/11 | Clean cross-section, camera never inside a vessel |
| 3b (1441–1680) | B3 | The muscle: green oxygen/energy dots stream into it and it contracts (shortens and bulges) (reference 21–23 s) | Slow orbit, f/11 | — |
| 4a (1681–1880) | B4 | Park: a man (yellow T-shirt with our logo, olive trousers) stands beside a fallen tree trunk, squats deep, puts both hands to its near side and heaves its thick end up to his waist (the thin end stays on the grass) | Wide 3/4 from the far side of the trunk, slow push | His hands are on the trunk's near side, hidden behind the trunk from every camera (LESSONS §2.15: hands framed out) |
| 4b (1881–2060) | B4 | Medium: he holds the trunk up at waist height, straining, logo on his chest above the trunk | Medium, from the far side, slight push | Same |
| 4c (2061–2200) | B4 | He lets go, steps his hands back, the trunk drops onto the grass, and he raises both arms in triumph (reference 27–30 s) | Front, push-in; logo flat to camera | The trunk falls only after both hands have left it |

## DA KRAS FILMS logo (1 placement)
- **L1, shots 4b–4c:** dark logo printed on the man's yellow T-shirt chest (the reference has text on his shirt), flat to
  camera in 4c, ~0.26 m wide, on screen > 2 s. Not in B1 (the trapped son).

## Characters (MPFB, appended unchanged from our finished packages; MakeHuman asset server still down, 502)
- **Mom**: `Inventor` (FrozenTearsGun v010), red blouse with white polka dots, blue jeans, brown ponytail.
- **Son**: `Teen` (HeadsetBullet v008), white T-shirt, dark-blue trousers.
- **Man**: `SpecF` (BelugaRescue v008), yellow T-shirt with logo, olive trousers.
- All: eye fix, camera-only catchlight per close shot, elbow IK limit opened (-40°…110°), hand-limit constraints,
  `hand_poses` presets (`hold_flat_object` under the bumper/trunk, `relaxed`, `open_alarm`), clothes in non-skin colours.

## Open questions for the director
1. **B4 subject.** The reference's last example is a man lifting a fallen tree off a **dog**. I built the man lifting the
   trunk without the dog (a rigged dog is extra risk and time). I can add a dog standing under the trunk if you want it.
2. **Son's age.** I used a teen. If the true story needs an adult son, I'll swap the donor.
