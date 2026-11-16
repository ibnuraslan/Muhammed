# Checks on the exact package `ScaldingCoffee_v002b_60fps.blend` (md5 7fce8c7eeb38e1a3a63665383a47ac84, frames 1–1808)

| Check | Result | Notes |
|---|---|---|
| `body_prop_cross` (step 3, per beat, every held or touched prop) | **0 solid crossings in every beat** | Steam volumes are gas, not solids: B1 `SpillSteam` over her lap (1–118) and B4 `Steam_C4` passing his face while he sips (1407–1470). Props: B1 cup, lid, car seats, door, dash, floor, wheel, roof lining, door trim; B3 bed, mattress, backrest, pillow, blanket, IV stand, cabinet, badge, **clipboard**; B4 logo cup, **3 phones**, counters, bar table, trays; B5 table, chairs, cup, sideboard; B6 knob, dial, machine, counters |
| `limb_check` (no-shoulder variant, step 4) | 0 arm/body; PROPHEAD ×14 = `Steam_C4` (the sip, gas) | |
| `clip_scan` (step 6) | Bad ranges **1–187** and **247–301** only (B1, seated woman, "self") | As v002: her hands resting on her lap; watched, no limb passes through her body |
| `qa_check` (step 6) | EMPTY/FILL on the product inserts; CAMJUMP ×14 = the hard cuts; PROPMOVE = the hands-free spill (151–163) | CLAW/FAN on C4's cup wrap and on the phone/clipboard pinches (the hand solver's intended grips) and the employee's knob pinch |

## Iterations to get here (all caught by the checks before any preview was approved)
1. Doctor's clipboard sank into his belly → held further out, upright, at his own shoulder height.
2. Phones: C2's in his chest, Hero2's fingers through it → placed from each person's shoulder, pinched at the side edge.
3. C1's and C5's cup grips put a thumb through the cup and the sip drove the cup into the head/chest → C1 checks a phone, C5 talks with bent arms, the sip moved to C4 whose wrap grip is clean.
4. C2's phone hand dipped into the counter top for 7 frames → drift up only.
