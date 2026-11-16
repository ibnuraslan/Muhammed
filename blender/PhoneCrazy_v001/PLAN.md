# B18 PhoneCrazy: shot plan (Phase 1, before the VO)

Film: 1080×1920, 60 fps, Cycles, hard cuts, one camera object (jump at every cut, smooth push/drift inside a shot).
Client direction (Nov 15): match the reference sheet (`briefs/batch2/B18_PhoneCrazy_reference_1fps.jpg`, 38 s) for shot order,
subjects, framing ideas and pacing. Times are reference seconds; Phase 2 moves every cut to the VO words
(`scripts/03_anim.py -- out.blend timing.json`). Every action is keyed at 1× from its shot start and runs ≥30% past the reference length
(the excavator, water swirl, phone buzz and screen schedules are continuous), so the VO can trim without stretching.

Cast (generic MPFB characters, eye fix, elbow limit opened, YXZ wrist limits, relaxed hands, yellow hard hats bone-parented to the head):
**Foreman** (lilac shirt, beige trousers, the phone's owner, as in the reference), **Digger** (black shirt, dark trousers), **Mate** (teal work suit).
Excavator: CC-BY articulated model (boom / stick / bucket keyed on a 4.4 s dig cycle), clean yellow paint, tinted cab glass (no driver visible).

**Key staging decision (risk "phone held in the fingers"):** the phone lies face-up on an orange site case the whole film.
"Unlocked itself / without anyone touching it" is shown literally: nobody touches it. No hand ever holds or touches the phone → zero grip risk.
Screens are an atlas of simple pictures (lock dots, app-tile grid, gallery, map, screenshot flash + thumbnail, keypad with dots, calling, glitch bands,
dark ripple): **no text, no digits, no real app or brand logos**. "911" is shown as the keypad keys lighting in 9-1-1 positions plus the call screen.
"45,000 gallons" is not shown as text: the full pit draining is the visual.

| # | Ref s | VO idea | Who / what physically happens | Camera | Risk → safe staging |
|---|---|---|---|---|---|
| 1 | 0–1 | As soon as (they started) | Wide dig site: excavator digging at the pit rim; crew of 3 by the case watching, Mate points at the machine | High wide from SW, slow push | Crew small in frame, faces 3/4 |
| 2 | 1–2 | digging | Bucket bites into the pit wall | Low from inside-pit side, push | Bucket into soil only |
| 3 | 2–5 | one of their phones unlocked itself | Phone on the case lid wakes, lock dots fill, padlock opens, home screen | Near top-down close, push | No hands near it |
| 4 | 5–6 | without anyone | Home screen of colour tiles | Top close, drift | — |
| 5 | 6–8 | touching it… watch | Crew around the case looking down: Foreman's open hand (surprise), Mate points at the phone, Digger turns his head. **Logo on the case front** | Low front, push | Hands ≥25 cm from the phone; no touch |
| 6 | 8–9 | as it opened apps | Gallery app opens, then a map app | Top close | — |
| 7 | 9–11 | snapped screenshots | White flash + shrinking thumbnail, twice | Angled close | — |
| 8 | 11–14 | tried to call 911 over and over | Keypad keys light 9-1-1, call pressed, calling screen pulses; phone buzzes on the lid | Close, push | Buzz = 1.6 mm / 1.2° jitter on the lid |
| 9 | 14–16 | again | High front-left: crew over the case, phone calling again (keypad → call). **Logo visible again** | High 3/4, drift | Faces readable 3/4 |
| 10 | 16–18 | digging in a pit | Pit full of water, crew and case in front, excavator behind | High wide, push | — |
| 11 | 18–19 | that mysteriously | Water starts to swirl, a dip forms | Closer, push | — |
| 12 | 19–20 | swallowed | Near top-down: vortex, level drops | High | — |
| 13 | 20–22 | 45,000 gallons of water | Last water drains away, crane up to show the pit's size | Crane up | No text |
| 14 | 22–24 | without a trace | Empty pit, dark drain hole in the bottom | Push to the hole | — |
| 15 | 24–26 | trying to see what was going on | Excavator digs into the pit | From across the pit | — |
| 16 | 26–28 | underneath the ground | Cut-away block: pit + excavator on top; soil layers, a shaft and a cavern with a blue stream flowing into a pool | Outside the block, slow dolly | Camera never inside soil; block 26 m deep so no empty band under it |
| 17 | 28–29 | until the phone | Foreman stares down at the phone, brows up, mouth parted, then looks up to the Digger | Low medium, push | Face under the hat brim: low camera |
| 18 | 29–31 | was going crazy | Screen glitches (RGB bands, jitter), phone buzzing | Top close | — |
| 19 | 31–33 | (it didn't look like a glitch) | Glitching keypad / call, other angle | Low-angle close | — |
| 20 | 33–35 | it was like something was inside | Dark ripple screen, push-in to the screen | Close push | — |
| 21 | 35–36.5 | trying to send | Keypad lights again → calling | Close | — |
| 22 | 36.5–38.5 | a message | Crew at the pit rim looking down into the drain hole | High from across the pit | Faces toward camera (looking down) |

**Logo:** DA KRAS FILMS (white version) printed on the front of the orange site case. Readable in S5 (2 s, flat to camera, ~20% of frame width)
and S9; small in S10. Not on the phone screen.

**Sets:** dig site at the origin (dirt ground with a 3.6 m-radius, 2 m-deep pit + drain hole, spoil heaps, grass beyond, Poly Haven sky);
cross-section block at x = 300. Rebuild: `scripts/build_all.sh` (~3 min).
