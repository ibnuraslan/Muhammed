# BalconyToddler: plan (Phase 1, before the VO)

ConnectB35. Branch `claude/connectB35-balcony-toddler`. 1080×1920, 60 fps, Cycles CPU, hard cuts (one camera per shot, timeline markers).
Reference: `briefs/batch2/B35_BalconyToddler_reference_1fps.jpg` (32 s). Same shot order, subjects and framing ideas, in our current look.
No on-screen text except our logo; no yellow measurement arrows, no neck highlight.

Phase 1 timing is provisional: every shot is animated at 1× from its own start frame, about 30% longer than its stretch of the
reference (`scripts/shots.py`, total 2570 frames ≈ 43 s). In Phase 2 the lengths become the VO frames and the build is re-run:
shots are trimmed (or extended at 1×), never stretched.

## Build
`scripts/01_lib.py` (cast + Poly Haven assets) → `scripts/02_build.py` (set, rigs) → `03_shots.py` (animation, cameras, markers) → `04_finish.py` (look, logo).

## Cast (MPFB, re-dressed copies of the approved ToddlerWell_v008 characters; MakeHuman's asset server is down from here)
- **Boy** (ToddlerWell "Toddler", ~0.76 m): pale-yellow sleepsuit, blue shoes. Head bone scaled 1.05.
- **Man** (ToddlerWell "Teen", no head torch): navy T-shirt and trousers. Climbs the tower and holds the legs.
- **Grandma** (ToddlerWell "Crowd1"): pink top, grey bob, fringe parted above the eyes.
- **Street people**: OldMan (white shirt), Woman (teal top), Lady (yellow), YoungMan (mustard jacket). All clothed in non-skin colours.
- Eye fix (cornea transparent mix) on every character, catchlight point light (camera-invisible) on every close-up camera,
  elbow IK limit opened, hand joint limits, relaxed hand presets, walks with arm swing.

## Set (one scene)
- Street: pavement, kerb, road with dashes, opposite houses with windows, a cafe opposite (awning, white sign board), street lamp,
  hydrant, potted plants, AC units.
- Apartment block: orange plastered facade (Poly Haven texture, softened), framed windows with curtains, ground-floor shop.
- **Balcony cage** on the 2nd floor: concrete slab (0.2 m) then a steel grille floor of round bars along X with a 14.5 cm clear gap,
  side/front frame tubes, corner posts, three rails (no rail at face height of the end shots), two struts under it.
- Apartment room behind the balcony door: laminate floor, blue-grey walls, sofa, rug, picture, ceiling lamp; open apartment
  door in the back wall with a hallway behind it.
- The tower: a Poly Haven wooden table with a wooden chair standing on it (backrest to the street, behind the climber);
  a second chair stands beside the table as a step; a third is carried in shot 12.

## Shot table (provisional frames)
| # | Ref | Words (ref captions) | Who, what they physically do | Camera |
|---|---|---|---|---|
| 01 | 0–1 | He slipped | Boy chest-deep in the grille gap, hands on the front floor bar, legs dangling and kicking under the cage. | Outside, above-front, looking down past the cage, 32 mm, small push. |
| 02 | 1–2 | through the bars | Same moment, legs kicking between/under the bars. | Low under the cage looking up, 30 mm. |
| 03 | 2–3 | of a second floor | Boy hanging under the cage (head held at the bars). | Wide across the street, whole 2nd-floor facade, slow push. |
| 04 | 3–4 | balcony | Same. | From the pavement, high crane-down to the cage. |
| 05 | 4–5 | His body fell | He slides down 17 cm until his head rests on the two bars (small settle), hands stay on the bar. | Front of the cage at bar height, 35 mm. |
| 06 | 5–6 | through the gap | He settles, head turns a little, legs sway. | Closer, front-left. |
| 07 | 6–7 | But his head | Close on his face above the bars, calm, small head turns. | 70 mm from 1.8 m, f/10. |
| 08 | 7–8 | got stuck | Head resting between the two bars (chin on the front one). | 3/4 side at bar level, 45 mm. |
| 09 | 8–10 | Leaving him hanging in the air | Whole boy under the cage, legs swaying. | Low front, looking up, 30 mm. |
| 10 | 10–11 | on the street | Four people on the pavement look up; the Lady points up at him. | Low behind them, building and boy above. |
| 11 | 11–12 | saw him | The man hurries toward the building (walk at speed, arm swing). Cafe sign with **logo** behind him. | Low ahead of him, he comes toward us. |
| 12 | 12–13 | And rushed to stack | Young man walks along the pavement carrying a chair by its seat edge (left hand). | Side, street level. |
| 13 | 13–14 | nearby chairs | Old man lowers the chair onto the table (both hands on the backrest top rail). | 3/4 front, chest height. |
| 14 | 14–15 | into a tower | Woman steadies the top chair (hand on its backrest) and looks up; old man steps back looking up. | Low 3/4, tower and boy above. |
| 15 | 15–16 | Then one man | The man steps up to the tower and looks up at the boy. | 3/4 low. |
| 16 | 16–17 | climbed up | On the top chair he rises from a crouch to standing, arms starting to come up. | Low angle from the pavement. |
| 17 | 17–18 | and grabbed | Close on his face looking up, arms rising. | 40 mm, push. |
| 18 | 18–20 | the boy's legs. Holding | His hands wrap the boy's shins (fingers closed on a static proxy of the legs); boy lifted 1.5 cm so the head is off the bars. | Low under the boy, looking up past the man. |
| 19 | 20–23 | to keep his neck from being crushed | Close on the boy, calm, head clear of the bars. | 48 mm, f/9. |
| 20 | 23–25 | For several minutes he held him up | Close on the man's hands on the shins. | 42 mm, f/9. |
| 21 | 25–26 | Until the boy's | Grandma walks in through the far apartment door; boy's head in the foreground at the bars. | Outside the cage at head height, looking into the room. |
| 22 | 26–27 | got inside | Grandma comes through the doorway into the room. | Inside, near the balcony door. |
| 23 | 27–28 | the apartment | Grandma hurries toward the balcony. | Inside, camera backs off in front of her. |
| 24 | 28–29 | And pulled | Grandma kneels on the slab and lifts him under the arms, out of the gap and back over the bars. | Outside front, between the rails. |
| 25 | 29–30 | the toddler back up | He stands on the slab, she kneels behind with her hands at his sides. | Outside front, chest height. |
| 26 | 30–32 | Completely unharmed | He looks up toward her, she leans her head down to him; camera pushes in. | Outside front, push-in. |

## Logo (DA KRAS FILMS)
One placement: dark logo on the white sign board of the cafe across the street, flat-on, seen behind the running man in shot 11
(and in the background of street shots that look away from the building). Never on a person, never in the close shots of the boy.

## Risky shots: simplest safe staging
- **Head between the bars (05–09, 19, 21):** the stuck height is calibrated in the script: head/neck vertices clear the two slot bars by 3 mm
  (contact, not through). The neck sits in the gap, chin over the front bar. Head turns are kept within ±6°.
  The gap (14.5 cm) is just wider than his chest and narrower than his (1.05×) head.
- **Calm, no distress:** neutral face, no neck strain shown, no close-up of the neck, no arrows or highlights.
- **Man's hands on the legs (18–20):** fingers are closed with `grip_object` onto a static mesh copy of the boy's legs at that pose
  (the boy holds still in these shots); his arms come up from below, no crossing of the boy's body.
- **Chairs (12–14):** the carried chair is keyed to the hand path (hand on the seat edge); the lowered chair is keyed and both hands are placed
  on its backrest rail at every key; the chair rests on the table top at the end (feet on the surface).
- **Grandma's lift (24–26):** palms on his chest sides just under the armpits (cup hold, 4 mm skin), fingers forward, elbows out;
  his arms are raised to the sides so nothing crosses. She kneels (knees on the slab, feet behind).
- **Camera:** no camera inside the cage or within ~0.6 m of a bar; the cage front is a thin tube; the rail at face height was removed
  so the end shots see both faces between rails.
