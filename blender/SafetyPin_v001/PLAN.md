# SafetyPin (B20): plan (checkpoint P1)

ConnectB20. Branch `claude/connectB20-safety-pin`. 1080×1920, 60 fps, Cycles CPU, hard cuts (one camera object per shot, bound with markers).
Reference: `briefs/batch2/B20_SafetyPin_reference_1fps.jpg` (34 s, current style). Shot order, subjects and framing follow it:
wire in fingertips → coil → finished pin → straight pin prick → two men admire the pin → worried inventor → desk hand-offs → boxes of pins → newspaper on a park bench.
VO not in yet. Each beat is its own 1× clip in its own frame window (about 30% longer than the reference beat). In Phase 2 each clip is
**shifted** (never stretched) so it starts on its VO word, then trimmed.

## Phase-1 timeline (clip windows; replaced by VO frames in Phase 2)
| Beat | Window (frames) | Ref. time | Story line |
|---|---|---|---|
| B1 wire → spring | 1–480 (8.0 s) | 0–6 s | He twisted a piece of wire into a coil, creating a spring that lets it open and close |
| B2 clasp | 481–810 (5.5 s) | 6–10 s | He then added a simple clasp to cover the sharp point |
| B3 straight pins hurt | 811–1200 (6.5 s) | 10–15 s | Before, straight pins caused injuries and infection |
| B4 first safety pin | 1201–1590 (6.5 s) | 15–20 s | This genius design … the first ever safety pin |
| B5 $15 debt | 1591–1860 (4.5 s) | 20–23.5 s | Desperate to pay off a $15 debt |
| B6 sold the patent | 1861–2220 (6.0 s) | 23.5–28 s | He sold the patent for just $400 |
| B7 made millions | 2221–2460 (4.0 s) | 28–31 s | Eventually the safety pin made millions |
| B8 died poor, respected | 2461–2730 (4.5 s) | 31–34 s | While he died a poor but respected inventor |

## Sets (one scene, sets far apart)
- **SetWork** (x = 0): 1840s workshop. Plaster walls with wood wainscot, plank floor, a daylight window (bright panes, never black), worn bookshelf with books,
  tall cabinet, chest of drawers with mantel clock and oil lamp, a long wooden workbench (Poly Haven table raised to 0.78 m), three stools,
  oil lamp, candlestick, wire spool. B1–B6 all happen at this bench.
- **SetStore** (x = 40): brick warehouse with 12 open cardboard boxes heaped with real instanced safety pins, crates and closed box stacks behind.
- **SetPark** (x = 80): lawn, path, park trees and shrubs, street lamp, painted wooden bench with a blank newspaper (columns of grey bars, a picture box with a safety-pin drawing, **no headline or text**), fallen leaves.

## Characters (MPFB, appended from our finished packages; eye fix, catchlight, elbow IK limit opened, hand limits, relaxed hands)
- **Hunt** (inventor): from BeethovenDeaf `Composer`; charcoal suit, dark brown hair. Donor x-ray shader, keyed skin fade and grey "aged" hair material stripped.
- **Pal** (young friend, the reference's green-jacket man): from PopeShot `GuardB`, re-dressed in a green suit.
- **Buyer**: from PrisonKeyCake `President`, brown suit, grey hair.

## Shot list (hard cuts; every shot has movement)
| Shot | Frames | Who / physical action | Camera | Risk → safe staging |
|---|---|---|---|---|
| 1a | 1–150 | Hunt seated at the bench, both hands at chest height pinch the two ends of a piece of wire; his left hand rolls back and forth (twisting) | Front medium, low, slow push-in | Wire ends sit in the measured gap between the thumb and index **skin pads** (1.7–2.2 mm gap, placed from the deformed mesh, not bones) |
| 1b | 151–330 | Close on the hands: the coil winds into the middle of the wire while he twists | Close 3/4 from above-front, f/11, slow push | Ends never move out of the pinch; the coil forms between the hands, not through a finger |
| 1c | 331–480 | Macro: the finished coil spring (point open, no clasp yet) pinched by its coil in his right fingertips; he turns it in the light; left hand rests on the bench | Macro, f/11, slow push | Re-staged (LESSONS §2.15): the two-hand "open/close" manipulation failed reach checks, so one hand turns the pin |
| 2a | 481–650 | Macro: the finished pin with its clasp head covering the point, turning in his fingertips | Macro, f/11, push toward the clasp | Same single-hand grip |
| 2b | 651–810 | He lifts the pin to look at it, head comes up, face to camera | Front medium, slow push | Pin in the fingertips below the hair line |
| 3a | 811–950 | Pal (green suit) holds a straight pin up and looks at it; left hand flat on folded cloth; pin cushion beside him | Front medium from his left, push | Straight pin pinched near the head |
| 3b | 951–1080 | He brings the pin down to the cloth, the point slips toward his left fingertip, he jerks the hand up | High 3/4 over the bench | Point stops a few mm off the skin (no pin into the finger) |
| 3c | 1081–1200 | He holds the fingertip up beside his face: a small red bead appears, a faint pink ring spreads (infection) | Medium close, f/8, slow push | Mild: one 3 mm bead, no wound, no blood flow; hand kept to the side of the face |
| 4a | 1201–1400 | Hunt (turned toward Pal) holds up the new safety pin; Pal leans in, studies it, looks up at Hunt and nods | Front two-shot, push | Pin pinched by its coil in Hunt's left fingertips |
| 4b | 1401–1590 | Close on Pal: looking at the pin, then at Hunt, nod | Medium close front-right | No props in Pal's hands |
| 5a | 1591–1740 | Hunt slumped at the bench, hands resting on it, slow head shake, a breath; debt note and three coins in front of him | Low front medium, push-in | Hands rest on the wood (no grips) |
| 5b | 1741–1860 | Insert: the blank debt note (lines only, red stamp ring, **no numbers**) and coins, his hands at the top of frame | High 3/4, push | No text on the note |
| 6a | 1861–2040 | Hunt and the Buyer face each other across the bench; Hunt's flat palm slides the patent paper (pin drawings, wax seal, no text) to the Buyer; the Buyer's flat palm slides a banded stack of blank green banknotes to Hunt | Side wide from Hunt's right | Flat-palm pushes only (no pinches); paper and money move only under a palm |
| 6b | 2041–2220 | Close on Hunt looking down at the money, then up | Front-left medium close | Buyer out of frame |
| 7a | 2221–2340 | Rows of open boxes heaped with safety pins, DA KRAS FILMS on every box | Low dolly along the boxes | Logo flat to camera, >15% frame width, >1 s |
| 7b | 2341–2460 | Crane up over the rows of pin-filled boxes | Crane up | — |
| 8a | 2461–2600 | Park bench with a newspaper, leaves drifting down | Low push-in | No text, no portrait (the paper's picture is the safety pin drawing) |
| 8b | 2601–2730 | Close on the newspaper's pin drawing with a real safety pin lying on it; a leaf lands | Slow push, f/9 | — |

## DA KRAS FILMS logo
- **L1, shots 7a/7b:** dark logo printed on the front of every pin box (flat to camera, about 30–40% of frame width in 7a, on screen 4 s).
- No second placement (the workshop is 1840s; the patent/debt/money stay blank). Never in B3 (injury) or B8 (death).

## Unsure / for the director
1. 1c/2a: the reference shows the second hand opening/closing the pin. I tried it (left fingertips following the moving point) and the reach errors were 3–14 cm, so I re-staged to one hand turning the pin. Open to cutting 1c to a different angle if you prefer.
2. The wire coil in 1b "winds in" between two fixed pinches (shape key). It reads as winding at preview size; at full res the wire gains length as it coils.
3. Pal's donor texture has the shirt and jacket at the same tone, so the whole suit is green with a lighter green shirt.
4. Hair on the reused rigs renders as a fairly solid cap (no fringe over the eyes).
