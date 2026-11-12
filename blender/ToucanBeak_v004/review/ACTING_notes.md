# ToucanBeak: acting review of v003, fixed in v004

Source: `before_v003_0p5s_0..2.jpg` (every 30 frames, 270×480, 8 samples).
Each item is listed with its v003 time and frame, then its fix. Story-beat frames (`beats.json`) are unchanged.

| # | Time / frames | Problem (against the acting bar) | Fix in v004 |
|---|---|---|---|
| 1 | 0.5 s / 31 | **The strike stick moves by itself.** Its held end is visible in frame with nothing holding it. | The stick is longer and pivots from far outside the frame: only the swung end and the impact are on screen, coming from off-screen above. |
| 2 | 1.5, 6.0, 8.0 s / 91, 361, 481 | **A tree trunk fills a third to half of the frame** (the hero trunk sits close to the lens). | The hero trunk is thinner and set back behind the branch end. The camera keys around 90 and 495 keep it out of the foreground. |
| 3 | 6.5 s / 391 | **The bird's head is cut** while the fig falls. The top-down frame shows only the yellow bib and a branch. | Re-aimed so the falling fig and the bird's head and stub beak are both in frame. |
| 4 | 9.0–9.5 s and clinic stay / 530–1960 | **VetA's right hand doesn't touch the bird.** It lies flat on the towel beside it. | The right hand rests on the bird's back (ray-cast surface contact, palm down, fingers over the back). The left hand steadies flat on the table beside the towel, clear of her own body. Contact is checked by the settle loop and the hand audit. |
| 5 | 9.0–11.5 s / 528–540 | **The scanner appears already in mid-air** when the camera arrives. | The scanner is in VetB's right hand from the first clinic frame, and the hand grips its handle. |
| 6 | 11.5–12.5 s / 680–760 | **The scanner moves by itself** to the table (its own keys, separate from the hand), and ends inside the table top. | The scanner rides on VetB's right wrist from 680 until he sets it down. It then rests upright on the table, on his right. |
| 7 | 12–25 s / 760–1500 (off camera, through the screen) | **VetB's idle right hand reaches across his body** to his left side and hangs in mid-air above the table. | The idle hands rest on his own sides of the table: right on his right, left on his left. |
| 8 | 11.0 s / 661–689 | **The frame is filled by the tabletop and VetA's forearm** during the move from the scan to the monitor. | The camera rises above the vets and keeps the bird, then the desk, in frame (re-keyed 672/689). |
| 9 | 11.5 s / 556–660 and 1562–1840 | **The assistant walks with no arm keys.** His IK hand targets stay at the world origin, pulling the arms. | Relaxed arm swing keyed from his shoulders while walking, and hands at the thighs when standing. |
| 10 | 25.0–25.5 s / 1505–1515 | **The assistant slides and teleports** from the desk to the far wall in 10 frames. It's visible through the monitor screen as the camera exits. | He stays at the desk through the exit, then walks away on planted feet (1566–1820) and stands with relaxed arms. |
| 11 | 25.5–26.0 s / 1515 | **The prosthetic pops into existence** in VetB's hand. | It sits on the exam table (on its cutting edge, at VetB's right) from the first clinic frame. He reaches for it at 1503, lifts it from 1510, and carries it to the stump. The hand follows it the whole way. |
| 12 | 26.5 s / 1585–1600 | **The camera sits right on top of the prosthetic in VetB's hand**: a blurred frame. | The 1600 framing is pulled back to show his hand, the prosthetic and the stump together. |
| 13 | 28.5–29.5 s / 1690–1800 | **The glue syringe appears out of nowhere** at the seam, and the glue bead pops on. | The syringe lies on the table at VetB's left. He picks it up (1717), lays the bead, and puts it back (1803). The syringe rides on his left wrist, corrected so the needle tip meets the seam within 1.2 cm. The bead grows around the seam as he works (Build modifier, 1736–1770). |
| 14 | 30.0 s / 1800–1810 | **The tweezers and pin appear in mid-air.** | Tweezers holding the pin lie on the table at VetB's right. He picks them up (1807), pushes the pin in (1910, within 1 mm of the target), and the pin stays in the beak. He sets the tweezers back down (1962). |
| 15 | 30.5 s / 1830 | **Fist-like grip on the tweezers.** | Pinch grip: thumb opposed, lower curl. |
| 16 | 25.0 s / 1496–1502 | **About 6 frames of empty sky** during the whip from the printer to the screen. | Kept short. The wall back and screen hole are framed sooner (key 1500). |
| 17 | 28.5 s / 1717 and 1803 | **Syringe pick-up and put-down read as a fist pressed into the table** (found in the first v004 close-ups): the fingertips were 4–5 cm under the tabletop, and the barrel lay beside the hand. | Pen grip from above, with the fingers along the barrel and the thumb on its side. The wrist is raised so the fingertips rest on the barrel, not in the table. Over 13 frames after pick-up, the barrel rolls in the fingers about its grip point into a pen angle, so the needle points at the seam. It rolls back before the put-down. The audit shows 0 hand/syringe penetration. |
| 18 | 9.0 s onward / 531–1960 | **VetA's resting left hand touched her own scrubs** (audit HAND_SELF). | The table rest point moved 6 cm out from her body. HAND_SELF is 0. |
| 19 | whole clinic | **Faces on the beats:** the vets' focused brows, lids and blinks read on beats 4 and 10. | Kept, with blinks staggered per person. |

The bird's motion was checked frame by frame and reads as real:
- planted feet on the perch, towel and platform (0 hover/sink in the audit)
- the flinch at impact with wing flare and follow-through
- two lunges at the fig, then frustrated head shakes
- calm breathing and small head turns while held
- pick-up, toss, catch and swallow at the end

## Verification on the final v004 build
- **Audit** (`audit_v004.txt`, every 2 frames, 1125 samples): 0 in every category. That covers toe hover and sink, hand into bird, hand into held prop, floating hand, hand vs hand, hand vs own body, hand vs other character, camera inside a mesh, and floating prop.
- **clip_scan** (`blender/pipeline/clip_scan.py` from the director branch, run at frame 600 so all 4 characters are found): `BAD_RANGES []`, so there are 0 bad ranges on camera. See `clip_scan_v004.json`. The small per-frame "other" counts on VetA are her right hand resting on the bird's back.
- **Hand close-ups** (`hands_closeups_v004.jpg`, 18 shots at 270×480): every hand contact, including each pick-up and put-down (prosthetic 1509, syringe 1717/1803, tweezers 1807/1962), the scanner grip, VetA's two hands, and the assistant's hand on the mouse.
- **Story-beat frames** in `beats.json` are unchanged.
- **Before and after sheets:** `before_v003_0p5s_0..2.jpg` and `after_v004_0p5s_0..2.jpg`.
