# ShoeBomber v011, check 3 (after fix round 2): FAIL. Fix rounds are used up.

`preview.mp4` is this check. It was rendered from the packed local `ShoeBomber_v011_60fps.blend` at 270x480, every 5th frame, with the VO.
A fresh reviewer gave a harsh PASS/FAIL on all 13 pages and failed 12 of them. Per the rebuild brief (at most 2 fix rounds), no .blend is pushed. Times are video seconds.

## Fixed since check 1 (confirmed in this preview)
- **Logo:** DA KRAS FILMS on the fuselage is readable for about 1.8 s (16.4–18.25). The tray logo is clean too, and the bulkhead logo appears briefly.
- **Waist:** no skin shows between the sweater and the trousers.
- **Trays:** they no longer overlap.
- **Takedown:** he now drops to his knees on screen (6.9–7.2).
- **Grab:** the steward's hands no longer wrap round him.
- **Cutaway:** frame 976 renders correctly.

## Still failing (reviewer, checked against the frames)
1. **Tackle, 6.5–7.6.**
   - PaxA's left forearm passes into his own torso (6.5–6.9).
   - The bomber's head meets the steward's head at 7.0, so it reads as a hug.
   - The actual fall to the floor happens during the whip to the attendant.
2. **Hands near the backside:** PaxA's hands on the lower back and waistband at 7.58 and 10.4–10.6.
3. **Overhead of the pinned man, 7.7–10.3:** the body runs sideways across the frame, which reads as a rolled horizon.
4. **Syringe, 8.7–9.9:** the needle stays a hand's width off the arm, and the steward's head is cropped at the neck.
5. **Finding the fuses, 10.7–13.3:**
   - Nobody handles the shoes.
   - The attendant's pointing finger reaches the armrest.
   - The two shoes are never read together in one clean frame.
6. **Attendant:** a doll-like face. No readable sniff, and the "caught him" beat is on the back of her head (4.9–6.3).
7. **Opening:** the bomber's face is out of frame for about 1.7 s during the match macro (0.8–2.5), and the flame never touches the fuse tip.
8. **Ending, 20.7–24.2:**
   - His shoes are already in his tray; no hand places them.
   - His arms are stiff, and the end shrug reads as an A-pose.
9. **Smaller faults:**
   - the steward idles still in the galley, 2.75–4.25
   - green-tinted shoe lining
   - the cloud deck reads as a flat blue slab, 18.3–18.9.

## Mandatory scene checks (run on the check-1 package; the staging is close to this one)
- `body_prop_cross` (ShoeL, ShoeR, Match, Syringe, Tray0): **0** visible crossings.
- `clip_scan` bad ranges:
  - 157
  - 397–421 (the grab)
  - 457–631 (the pin)
  - 691–709 (the pointing hand)
- `qa_check`:
  - EMPTY 135, FAN 67 and INSIDE 15: mostly the void, sky and macro beats, which have no faces.
  - CAMJUMP 2: the set swaps inside the whips.
  - PROPMOVE 6, BACKHEAD 1, CLAW 1, FILL 1.
- `limb_check`: ARMBODY 1059 and ARMBACK 18. Not triaged. The prone, cuffed arms are the likely bulk.

## Recommended next step (director's call)
Restage beats 4–6 more simply:
- One captor only, kneeling on the far side, with hands on the shoulder blades.
- An upright overhead with his head at the top of the frame.
- The needle keyed into the deltoid as a macro, with the hand out of frame.
- The attendant lifting a shoe from the seat in a posed grip, or a two-shoe macro on the seat with nobody's hand in it.
- The airport payoff ending on the logo tray with the shoes in it.
