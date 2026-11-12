# WW1Assassination: acting review of v004 (half-second sheet, 270×480, 8 spp)

Sheets: `ACTING_v004_sheet_0-18s.jpg` and `ACTING_v004_sheet_18-36s.jpg` (before), and `ACTING_v005_sheet_*.jpg` (after). Times are film seconds (frame = 1 + 60·t). The beat start frames are unchanged in v005 (see `beats.json`).

| # | Time (frames) | Problem in v004 | Fix in v005 |
|---|---|---|---|
| 1 | 12.5–13.5 s (750–810) and the whole bomb beat | A crowd extra in overalls stands **inside the bomber**: two bodies merged on the same spot. It reads as a man in overalls throwing, and the real bomber (suit, fedora) is hidden in him. The crowd placement never excluded the principals' spots. | Crowd homes now keep ≥1.3 m clear of every principal's position (bomber, both would-be assassins, gunman, officer, horses). |
| 2 | 3.5 s (≈211) | The camera arc over the front seat puts the **driver's cap filling the lower frame**. | The arc is raised (z 2.4 → 2.8) and moved toward the Archduke's side, so the driver's head stays at the frame edge. |
| 3 | 7.5 s (≈451) | Start of the rewind: the frame is filled by the **café's corner wall** and awning. | The rewind path now stays over the side-street road (x 0.5–2.5) and looks along the reversing car, then sweeps east over the quay. |
| 4 | 14.5 s (≈871) | No readable subject: the camera looks across the river while the bomb is a speck. | The camera moves 2 m closer (north of the car lane, low), with a 35 mm lens on the bomb as it lands. |
| 5 | 25.0–25.8 s (1501–1549), the shots | Over-the-shoulder framing: the gunman's back and head fill 40 % of the frame and **hide the pistol and the muzzle flashes**. | The camera moves to his right side (pistol side): the arm, pistol and both flashes read, with the couple in frame. |
| 6 | 26.5–27.0 s (1591–1621), "killing the Archduke and his wife" | The camera passes in front of the car's bonnet. The frame is the driver and the dashboard; **the couple's slump is not readable**. | A new framing beside the car at rear-seat height (west side): both slumps and faces read, then the camera rises. |
| 7 | 13.0 s | The bomb hand: the bomber's grip is hidden (see #1). | Resolved by #1. The bomber's right hand visibly holds the ball until release (close-up in `hand_closeups.jpg`). |
| 8 | 18.5 s | The scattered crowd stops and stands stiffly after the run. | Kept, but they idle (sway, breathe) and look at the wreck. This is in v004 already; checked. |

## Further problems found by `pipeline/clip_scan.py` on v004 (6 bad ranges) and fixed in v005
| # | Time | Problem | Fix |
|---|---|---|---|
| 9 | 0–3.6 s, 4.8–7.3 s, 21–22 s, 24.8–26 s | The **Archduke's resting fingers sink 3–5 cm into his thighs**: the hands rest "on the knees" but inside the legs (~340 finger vertices). | Hands are lifted onto the top of the thighs with a flatter resting curl (6°). When slumped, they fall beside the thighs onto the seat. |
| 10 | 2.3–5.4 s, 21.3 s | The **Duchess's inner hand reaches into the Archduke**: her elbow pole pulled the arm across. | Inner elbow pole moved back; lap hand moved slightly toward her own side. |
| 11 | 5.9–7.1 s, 24.8–25.4 s | The Duchess's frightened **hand-to-chest goes into her chest**. | The hand rests on the chest surface, 11 cm further forward. |
| 12 | 0.6–2 s, 7.3–7.8 s (crowd) | Crowd idle hands: **curled fingers into their own thighs**. | Idle hands hang 4 cm further out, with a lighter curl (12–20°). |
| 13 | 7.5 s (rewind) | The gunman's **drawing hand sits inside his chest**. | The draw starts from in front of the coat. |
| 14 | 27–29 s | After the shots the officer pulls the gunman back **onto the officer's own spot: the two bodies overlap** (64 hand-audit hits). | The officer grabs from the gunman's right side and ends 0.5 m away. The gunman only staggers 0.2 m into the grip. |
| 15 | 7.7 s (rewind, far) | Two fleeing bomb-site extras **end up touching**. | Flee targets are kept ≥1 m from every other person's spot. |
| 17 | 25.0–26.5 s | Re-check after fix #5: the side framing lost the pistol, and the slump framing sat behind the Duchess (hat brim and folded roof filled the frame). The Archduke's slumping hands and the Duchess's inner hand also touched each other (26.0–26.4 s). | A higher over-the-shoulder lines up the pistol hand with the Archduke, and the flash lights the couple. The slump is framed front-left, three-quarter. His inner hand stays on his thigh and his outer hand drops onto the seat. |
| 16 | 14.5 s | Re-check after fix #4: the camera aim drifted between keys, so the bomb was still out of frame. | Two aim keys lock onto the falling object (14.4 s, 14.85 s): it hits the roof, drops, and rolls toward car 2, all in frame. |

## Mandatory self-check (director, 14:40 UTC): problems found by looking at the images, fixed in v005
| # | Time | Problem | Fix |
|---|---|---|---|
| 18 | 12.5 s (beat 5) | The cell is mostly a bare shop wall. | A new key lands on the bomber at 12.35 s. |
| 19 | 18.5 s (beat 7) | The cell is mostly empty cobbles. | A new key swoops onto the car as it leaves along the quay. |
| 20 | 25.0 s (beat 9) | The back of the gunman's head fills the foreground. | A front three-quarter on his face and the extended pistol arm; the flash lights him. |
| 21 | 29.5 s | Cloud blur. | The clouds are fully clear by 29.4 s, so the cell is the crisp map. |
| 22 | 11 s | The would-be assassin's hand floats as a claw 3–4 cm in front of his chest. | His palm is keyed onto the coat surface every frame, with a relaxed curl. |
| 23 | 27–29 s | The officer's fists hover beside the gunman's arm without touching it; the far hand floats in the air. | One-handed grab: his near hand is keyed onto the gunman's actual upper arm every frame; the far hand hangs relaxed at his hip. |
| 24 | parasol | The shaft ran beside the Duchess's hand, not through it. | The parasol is re-seated so the shaft passes through her closed hand, between thumb and index finger. |
| 25 | close-ups | Three close-ups were blocked or black: the camera was inside the car or a wall. | The close-ups are now aimed at each wrist (`hand_closeups.jpg`, 8 hands). |

## Result
- **clip_scan** (`v005_clip_scan.json`, step 6): **0 bad ranges** (v004: 6, in `v004_clip_scan.json`).
- **Hand audit** (`v005_hand_audit.txt`): 14, all of them:
  - 7 palm-on-coat at the would-be assassin's chest, which is intended contact;
  - 7 fleeting fingertip brushes between fleeing extras, seen at more than 40 m.
- **Hand close-ups:** `../../WW1Assassination_v005/hand_closeups.jpg`.

## Checked and fine
- **Feet:** planted (walk solver, 0 slides). The audit's worst foot sink is 4.4 cm on 3 crowd people.
- **Couple:** seated inside the car, with hands on laps and knees, the parasol held, and smile, shock and slump faces.
- **Driver:** hands on the wheel (IK within 3.6 cm).
- **Grips:** the pistol, bomb and parasol are all held by a hand with a grip curl; no prop moves on its own (the bomb is held until release, then follows a ballistic arc).
- **Officer's grab:** on the gunman's upper arm.
- **Intended effects, not acting faults:**
  - The rewind (7–10 s) plays the whole world backwards, so people walk backwards.
  - The fast-forward at 19–20 s happens with the camera high overhead.
