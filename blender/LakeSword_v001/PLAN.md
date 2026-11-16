# LakeSword: plan (Phase 1, before the VO)

ConnectB34. Branch `claude/connectB34-lake-sword`. 1080×1920, 60 fps, Cycles CPU, hard cuts (one camera per shot, bound by a
timeline marker at its first frame). Reference: `briefs/batch2/B34_LakeSword_reference_1fps.jpg` (36 s, 1 frame/s). Client
direction (Nov 15): match its shot order, subjects and framing ideas, in our current look.

Phase 1 timing is provisional: each shot is animated at 1× in its own frame range, about 30% longer than the matching stretch
of the reference (frames 1–2710, ~45 s). In Phase 2 the shot table in `scripts/03_shots.py` gets the VO frames (`shots.json`)
and the build is re-run: every shot keeps its 1× animation and is only trimmed (or extended at 1×), never stretched.

Build: `01_chars.py` → `02_sets.py` → `03_shots.py` (helpers: `lib_shots.py` from ConnectB07, `pipeline/anim_lib.py`,
`pipeline/hand_poses.py`). Review: `frames.py` + `sheet.py`.

## Cast (MPFB rigs re-used from our packages; eye fix on all six, elbow IK limit opened, relaxed hands)
- **Girl**: BelugaRescue "SpecC" (small girl, ~1 m), blonde ponytail (no fringe), pink-purple T-shirt, pale grey trousers, pink shoes.
- **Dad**: EscapeArtist "Father", grey shirt, navy jeans, fair hair.
- **Expert M**: EscapeArtist "Judge", dark suit, white shirt, tie. **Expert F**: EscapeArtist "Protester1", auburn hair tied back
  (no fringe), striped blouse, dark skirt.
- **Warrior** (long ago): EscapeArtist "Guard2", green wool tunic, brown trousers, leather belt, sheathed sword on his left hip.
  **Companion** (background): EscapeArtist "Protester2", blue-grey tunic, brown trousers, belt.

## Sets (one scene, far apart; camera clip_end 80 m so no other set shows on a horizon)
1. **Lake** (x=0): shallow clear water (z=0) over a sandy bed (−0.25 m), sandy/grassy bank, pines and firs (Poly Haven),
   mossy rocks, grass and ferns, far shore with pines. Sun + clear partly-cloudy sky.
2. **Museum** (x=100): white hall, wood floor, wooden display table with green felt, pedestals, framed pictures, a wooden crate,
   ceiling light panels, deep-red banner on the back wall.
3. **Macro** (x=200): sky-blue gradient dome (#4FC3F7-ish to near white) with three soft area lights.
4. **Camp** (x=300): lakeside camp of the past: two canvas tents (CC-BY), two wooden boats (one beached, one afloat), stone fire pit
   with a small stylised fire, pines, sandy shore, grass.

**The sword** (one model everywhere, CC-BY "Viking Sword"): found = rusted iron hilt with a crusty brown shell over the blade
(the "rust" is the old sheath, so it reads as a stick); warrior = the same sword in clean steel inside a clean leather sheath; the
macro shows the crust turning into the leather sheath with an embossed interlace pattern (no letters, no date text).

## Shot table (provisional frames, 60 fps)
| # | Frames | Ref s | Ref caption | Who / what they physically do | Camera |
|---|---|---|---|---|---|
| 01 | 1–110 | 0–1 | "The girl" | Girl wades toward camera through the shallows, arms swinging. | Low at the water line, 30 mm, slow push-in. Full body. |
| 02 | 111–220 | 1–2 | "something solid" | She steps; her right foot comes down beside the hilt sticking out of the sand; she stops and looks down. | High front, 28 mm, her face and the foot by the hilt under clear water. |
| 03a | 221–370 | 2–4 | "while playing in the shallow water" | She kicks two splashes with her right foot, arms out for balance, head turning. | Front wide-medium, slow push-in, shore and pines behind. |
| 03b | 371–500 | 4–5 | "in the shallow water" | She looks down into the water, head turning, small sway. | Front-left diagonal medium, slow push. |
| 04 | 501–640 | 5–7 | "it seemed" | She bends and reaches into the water; her right hand closes on the hilt just under the surface; left hand on her knee side. | Low side near the water, 32 mm. |
| 05 | 641–780 | 7–8 | "pulled it out" | She straightens up pulling the long crusty "stick" out, then takes it in both hands (right on the grip, left on the crusted blade, 30 cm apart). | Front medium, slight push. |
| 06 | 781–920 | 9–10 | "it was actually a sword" | She holds it upright at her right side (right hand on the grip, thumb up), left arm relaxed, and looks up along it. | Low front push-in. |
| 07 | 921–1040 | 11–12 | "looked like rust and chipped" | Close: the crusty blade upright at frame left (same one-hand hold), her face beside it, clear of the blade. | Close, 40 mm, slow drift. |
| 08 | 1041–1210 | 13–14 | "when she showed her dad" | On the shore. Dad **kneels** to her height, arms at his sides, and leans in to look; she shows him the sword upright at her side. **No hand-off on screen**: the cut to 09 carries it (see risky shots). | Side three-quarter, low medium. |
| 09 | 1211–1350 | 15–16 | "he realized it could be (valuable)" | Still kneeling, he holds it level in both hands (right wraps the grip, left wraps the crusted blade from below) at chest height, looks along it, amazed. | Very low, against the blue sky, slow orbit. |
| 10 | 1351–1500 | 17–18 | "so they took it to a museum" | Museum wide: the sword on the felt; Expert M leans over it (hands at his sides, not touching the table), Expert F looks down, girl and dad at the table end. **Logo 1** on the red banner behind. | Wide three-quarter, slow push-in. |
| 11 | 1501–1670 | 19–21 | "and experts told the girl her sword" | Expert F holds the sword level above the table in both hands (wrap grips) and raises it a little; Expert M leans in studying it; the girl watches. Banner (logo) behind. | Front medium. |
| 12 | 1671–1810 | 22–24 | "was a thousand years old" | Closer: the experts look up from the sword to each other and nod (no date text). | Close two-shot. |
| 13 | 1811–1940 | 25–26 | "and what looked like rust" | The crusty blade on the sky-blue gradient. | Macro glide along the blade, f/11. |
| 14 | 1941–2090 | 27–28 | "was actually a leather sheath" | The crust gives way to an old leather sheath with an embossed interlace pattern. | Macro glide back toward the hilt, f/11. |
| 15 | 2091–2250 | 29–30 | "It had belonged to a warrior" | Camp long ago: the warrior walks toward camera along the shore, sheathed sword on his left hip (on the belt, bone-parented); a companion crosses behind. | Medium, tracking back. |
| 16 | 2251–2410 | 31–33 | "and dated back before the Vikings" | Wide camp: tents, boats, fire; the warrior stops near the water and looks out over the lake. | Wide, crane up. |
| 17 | 2411–2560 | 34–35 | "somehow ending up in the lake" | The sheathed sword drops into the lake beside the boat (ripple), sinks through the clear water and settles on the bed. | High angle over the water. |
| 18 | 2561–2710 | 36 | "until she found it" | Today: the girl wades along the shallows, arms swinging. | Front three-quarter, low. |

## Logo (DA KRAS FILMS), 2 placements, both in the museum (no logo at the lake, on the girl, or in the past)
1. White logo on the deep-red banner on the back wall (2.0 m wide), flat-on in shots 10–12, sharp (f/8).
2. Dark logo on the side of the wooden crate in the museum (shot 10 background).

## Risky shots and the simplest safe staging
- **Small hands on the sword (04–08):** the grip is solved with `grip_object` and the sword is pinned to the wrist (Child Of).
  The girl's short arm misses the IK target by 2–9 cm, so after the grip solve the sword is snapped to the hand the IK actually
  reached (otherwise it floated beside the hand). Two hands only in 05, 30 cm apart (grip and crusted blade). In 06–08 she holds
  it **one-handed, upright at her right side**, after a two-hand version put her left arm through her body and the blade over her
  face.
- **Dad's hand-off (08 → 09):** a flat-palm hand-off was tried twice: dad's arm folded behind him, and the sword tipped. Simplest
  re-stage: no exchange on screen. She shows it to her kneeling dad (08), then a hard cut to him holding it (09). If you want the
  exchange itself, I'd stage it as a short side cut-in of only his flat palms coming under the blade.
- **Experts (10–12):** Expert M never touches the table (his forearm crossed the table edge); Expert F holds it in two wrap grips,
  never a two-person grip.
- **No "1020 A.D." text** anywhere; the age is told by the experts' reaction.
- **Warrior (15–16):** the sword hangs in its sheath from the belt (bone-parented to the pelvis), behind his left hand, never in the
  air, no hand on it.
- **Sinking sword (17):** it drops into the lake beside the boat (ripple), decelerates in the water and settles on the bed; no hands.
- **Child in water:** calm, playful, no distress.

## P1 status (checks on the provisional build, frames 1–2710)
- Sheet: `review/P1_3perShot_540x960_p1.jpg` (shots 01–10) and `_p2.jpg` (10–18): first / middle / last frame of every shot,
  540×960, Cycles 8 samples, labelled with shot and frame.
- `review/P1_body_prop_cross.json` (step 3, every sword copy and sheath, the felt and the table). Cleared since the first run:
  the girl's thigh and arm through the sword (06/07), Expert M's forearm through the table (10/11), the warrior's arm through
  his belt sword (15/16), dad's arm folding behind him (08).
- **Still flagged (hand-in-grip only):** thumb tips sink into the grip in 04–06; in the adult two-hand holds (09, 11, 12)
  knuckles/metacarpals sink into the crusty sheath. Planned fix: solve the wrap against the sheath's real thickness (shell
  pushed out 4.5 mm), back the palm off until the metacarpals clear, then re-check with body_prop_cross; if it is not clean
  after that one retry, the experts hold it on a cloth-covered tray and dad's hold is framed from the side.
