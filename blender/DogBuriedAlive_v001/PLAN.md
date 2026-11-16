# DogBuriedAlive: plan (Phase 1, before the VO)

ConnectB21. Branch `claude/connectB21-dog-buried-alive`. 1080×1920, 60 fps, Cycles CPU, hard cuts, one camera per shot.
Reference: `briefs/batch2/B21_DogBuriedAlive_reference_1fps.jpg` (28 s). Same shot order, subjects and framing ideas,
in our current look. Phase 1 lengths are provisional (about 1.3–1.5× the reference stretch); every shot is keyed at 1× from
its own start frame, so Phase 2 only trims or extends shots to the VO frames (`scripts/shots.py`), never stretches them.

## Cast and sets
- **Dog**: the real Labrador model (Sketchfab CC-BY, Yury Misiyuk) on our quadruped rig, the same model SpeakWithoutSight
  and B01 used, cream-golden coat everywhere (one model, one colour in every shot). Fur-coloured eyelid caps (bone-parented
  to the head) close his eyes while he is unconscious and open on "woke up".
- **Dad** (navy shirt/trousers), **Mom** (mustard top, light shorts), **Son** (red tee): MPFB rigs reused from Tsunami2004
  (TouristM, LocalW, KidA), eye fix applied, elbow IK limit opened, relaxed hands, non-skin clothes.
- **Sets** (one scene, far apart):
  1. **Grave cross-section** (x=0): a cut through the lawn: real soil-wall texture (Poly Haven), the backfilled pit in loose
     red dirt, an air pocket around the lying dog, grass along the top edge, the house far behind, spoil heap + shovel.
  2. **Road** (x=100): asphalt road with edge lines, grass verges, houses, shrubs; red pickup (CC-BY, text-free).
  3. **Yard** (x=200): blue-and-white two-storey house with porch (CC-BY), lawn, concrete driveway, street, neighbours,
     the grave mound with a shovel; the family's blue SUV (CC-BY, repainted, plates blank).
  4. **Porch close-up** (x=300): grey plank deck, light-blue lap siding, white french doors (as in the reference), posts, steps.

## Shot table (provisional, 60 fps)
| # | Ref s | Ref caption | Shot: who, what they physically do | Camera |
|---|---|---|---|---|
| G01 | 0–1 | "They buried" | Cross-section: the dog lies on his side in a pocket at the bottom of the pit, eyes closed. Clumps of dirt fall in from above and the loose fill rises over him. Mom, Dad, Son stand at the edge above, heads bowed: Mom's hand to her mouth, Dad's arm round the boy (hand on his upper back). | Low on the cut face, 40 mm, slow push-in. |
| G02 | 1–2 | "but didn't notice" | Closer: the dog breathing (ribs move) while the last clumps land on the fill above. | 32 mm, slow push toward the dog. |
| G03 | 2–5 | "the dirt moving … walked away" | Wide: the mound is finished; the family turn and walk away across the lawn (arms swing), the dog still breathing below. | Crane up slightly as they leave. |
| R04 | 5–6 | "the dog (had been hit)" | Flashback: the dog trots along the road toward camera, the red pickup behind him. Cut before any contact. | Low at the roadside, tracking back. |
| R05 | 6–7 | "by a truck" | Soft cut: the dog lies still on his side at the road edge, eyes closed, no wound; the pickup stopped behind. | High 3/4 view, slow descent. |
| Y06 | 7–9 | "thinking he was dead" | Lawn in front of the house: the dog lies on his side; Dad stands over him bent forward, head bowed; Mom (hand to her mouth) and Son stand behind, sad. No hand on the dog. (A one-knee kneel was tried and read badly; dropped.) | Low front, slow push. |
| Y07 | 9–10 | "buried him" | Fresh dirt mound in the lawn; the family stand around it, heads bowed; Mom's hand to her mouth, Dad's arm round the boy. (The only shovel asset read as a bucket: dropped.) | Low, slow push. |
| Y08 | 10–11 | "then left" | The blue SUV backs out of the driveway. **Logo (white) on the front doors.** | Lawn, pans with the car. |
| Y09 | 11–12 | "for the weekend" | The SUV drives off along the street, logo side to camera. | Tracking alongside. |
| U10 | 12–13 | "he was actually just unconscious" | Underground close-up: his head in the pocket, eyes closed, breathing. | 40 mm f/9, slow push. |
| U11 | 13–14 | "when he woke up" | His eyes open, ears/head twitch, breathing quickens. | Same, closer. |
| U12 | 14–15 | "underground" | He lifts his head and looks up toward the surface. | Medium on the pocket. |
| U13 | 15–18 | "he clawed his way back up" | One tall tunnel: his back to camera, nose up, front paws dig alternately; small dirt clods drop from his paws; he climbs toward the surface. | Medium, crane up with him. |
| Y14 | 18–19 | "to the surface" | Yard: his head and front paws push out of the mound; small clods crumble down the mound's sides. | Low front, small push. |
| Y15 | 19–21 | "the family, days later" | The SUV turns in from the street and pulls into the driveway. | From the lawn. |
| Y16 | 21–22 | "they found him" | Foreground: the dog stands by the porch steps, tail wagging, watching the SUV roll to a stop. | Low behind/beside the dog. |
| P17 | 22–23 | "on the porch" | The dog stands on the porch in front of the white french doors, tail wagging, panting. | Low front, push-in. |
| P18 | 23–24 | "wagging his tail" | Side view: the tail wags hard, he takes a step forward and tilts his head. | Side, slight arc. |
| P19 | 24–26 | "he was happy" | Face close-up: head tilts, panting, happy. | 40 mm f/9, push-in. |
| Y20 | 26–27 | "horrified" | By the parked SUV: the family see the dog trotting up to them; they step back, hands come up in front of their chests (palms out), mouths open. Faces readable. | From behind/beside the dog, low. |
| Y21 | 27–28 | "horrified" | Closer on the family's horrified faces (hands up in front of the chest, mouths open). | Medium close. |

Provisional total: 2480 frames (41.3 s). The VO decides.

## Logo (DA KRAS FILMS)
One placement, on the SUV's front doors (white version on the blue paint, both sides), seen in Y08, Y09 and Y15
(the reference has its logo on the SUV door too). Never on a person, the dog, the grave or the "dead" beats.

## Risky shots and the safe staging used
- **Dog lying (G01–G03, R05, Y06, U10–U12)**: one clean curled pose everywhere: on his side, spine curved, legs folded,
  head down toward the front paws, eyelids closed. In the pocket he faces the open cut, clear of every wall.
- **Truck hit**: never shown. R04 cuts while the truck is still 5 m behind; R05 is a soft cut to him lying still.
- **Paws clawing up without passing through the soil**: in U13 the pocket stretches into one tall tunnel around his whole
  climb, so his body and paws are always in open space; the clods are small separate dirt lumps that fall down.
- **Owners' faces readable at the reveal**: Y20/Y21 are framed from the dog's side, so the family face the camera.
- **Hands**: nobody touches the dog or holds a prop. The only contacts are Dad's hand on the boy's upper back (from behind) and
  Mom's hand 5 cm in front of her mouth.

## P1 status (P1b after the director's notes)
- Sheet: `review/P1b_stills_3perShot_540x960_sheet.jpg` (P1 was `review/P1_stills_3perShot_540x960_sheet.jpg`) (first/middle/last frame of all 21 shots, 540×960, Cycles 8 samples).
- `body_prop_cross` (step 3, all frames, props SUVcar, PickupCar, HouseY, GraveMound, MoundY, Backfill): **0 visible crossings**
  (`review/P1b_body_prop_cross.json`). There are no held props in this film.
- Build: `scripts/01_lib.py` (assets) → `scripts/02_build.py` (+ `02_sets.py`, `03_shots.py`, `shots.py`). The .blend is not
  committed at P1; it is rebuilt from the scripts in about 6 minutes and packed at Phase 2.

## P1b changes (director notes, 5c88493)
1. Lying pose: one curled side-lying pose in every lying beat (no crossed legs, no belly-up).
2. U10/U11: framed head and shoulders from above the open cut; eyelids closed in U10, they open in U11.
3. U13/Y14: one tall tunnel, back-to-camera climb, small dirt-coloured clods that only fall down.
4. Coat continuity: key/fill lights added on the porch and road sets so the coat reads the same cream as in the yard.
5. Family: Mom's hand to her mouth, Dad's arm round the boy, heads bowed (G01, G03 start, Y06, Y07).
6. Y20 starts with the dog fully in frame; P18 has a step and a head tilt.
