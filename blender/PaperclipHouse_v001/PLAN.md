# B36 PaperclipHouse: Phase 1 plan (Connect B36)

**Reference:** `briefs/batch2/B36_PaperclipHouse_reference_1fps.jpg` (current style, 57 s). We follow its shot order, subjects and pacing: one hero in a purple top trading item by item with a new partner in each place, then the house.

**Format:** 1080×1920, 60 fps, Cycles, hard cuts (one camera per shot, switched by timeline markers).

**Clips:** each shot is its own 1× clip about 30% longer than its expected beat (`scripts/03_anim.py`, `SHOTS` table). In Phase 2 the clips go onto the VO frames and only their tails are trimmed. Nothing is time-stretched.

**Build:** `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` → `04_lights.py` → `pipeline/anim_look.py --no-sky`. Props come from `scripts/10_props.py`.

## Cast
All characters are MPFB rigs reused from our delivered packages and re-dressed. Every one has the eye fix, hand and wrist limits, the elbow IK limit opened to −40°, and a ≤1.5 W camera catchlight.

| Role | Look | Shots |
|---|---|---|
| **Hero** | purple long-sleeve top, jeans, brown hair | every shot except S23 and S25 |
| PenLady | long hair, red-striped blouse, grey skirt | S01; also reads the paper in S23 |
| KnobMan | denim shirt, jeans | S03 |
| Camper | green field jacket, afro | S05; party guest in S08 |
| Worker | blue work overalls, white tee | S06; party guest in S08 |
| KegGuy | green-striped shirt | S07, S08 |
| SledGuy | red-orange top | S09 |
| VanGuy | red-striped shirt | S12 |
| Exec | charcoal suit and tie | S14 |
| Landlady | long hair, blue-striped blouse | S15 |
| Rocker | all-black jacket and jeans | S17–S19 |
| Director | navy suit | S21, S22 |
| Mayor | olive overalls, white tee | S23 (newspaper), S27 |

## Sets
Each set sits at its own world offset with its floor at z = 0.

| Set | Contents | Shots |
|---|---|---|
| HOME | blue kitchen: counter, cabinets, two sky windows, sofa, dining table, shelf, plant. Also used as the new home's interior in S29. | S01, S02, S29 |
| OFFICE | classroom/office: green board (blank), metal desk, desk lamp, bookshelf, window | S03, S04 |
| CAMP | grass meadow, fir forest, blue dome tent, picnic table, stone fire pit | S05 |
| STREET | suburban street, houses, drives, lamps, firs, blue mailbox (no text) | S06, S15, S16, S23, S26–S28 |
| GARAGE | roller door, steel shelves, tool chest, tool cart, hanging lamps; party bulbs, balloons, cups; logo box | S07–S09 |
| SNOW | snow field, trail with orange-tipped marker posts, firs, snowy mountains | S10–S13 |
| STUDIO | blue studio. Record corner (desk), bar corner (bar, stools, TV), film corner (flood lights, movie camera, armchair) | S14, S17–S22 |
| VOID | bright sky-blue gradient stage (explainer) | S24, S25 |

## Shots
Each trade is a hand-to-hand swap:
- **Small items:** the hero's right hand gives his item to the partner's left hand while the partner's right hand gives the new item to the hero's left hand. Both hands are on each item for about 0.3 s.
- **Big items** (stove, generator, keg): two hands each on the item's side faces.
- **Grip:** while a hand holds an item, the item is re-keyed every frame from that hand's evaluated wrist: the giver's until the release, then the receiver's.

| Shot | Beat (reference words) | Set | Who and what they physically do | Camera | Clip (f) |
|---|---|---|---|---|---|
| S01 | He traded a red paperclip… | HOME | Hero behind the counter, facing camera; PenLady in front (¾ back). Paperclip goes hero → her, fish pen goes her → hero, across the counter. | ¾ medium from the front-left, push-in, 32 mm | 187 |
| S02 | …for a pen in the shape of a fish | HOME | CU: hero turns the fish pen in his fingers and smiles. | CU push, 50 mm f/9 | 117 |
| S03 | was later exchanged for a custom doorknob | OFFICE | Hero and KnobMan swap the fish pen for the doorknob in front of the desk and board. | medium two-shot, push, 35 mm | 187 |
| S04 | (doorknob) | OFFICE | CU: hero lifts the doorknob in his left hand and looks at it. | CU push, 50 mm f/9 | 101 |
| S05 | Next he traded it for a camp stove | CAMP | Camper hands over the open camp stove (two hands each); the doorknob lies on the picnic table behind. | medium two-shot, push, 35 mm | 187 |
| S06 | and then a generator | STREET drive | Worker hands over the red generator (two hands each); the stove sits on the drive. | medium two-shot, 35 mm | 187 |
| S07 | and the generator for a keg party… | GARAGE | KegGuy hands over the steel keg; the generator stands on the floor. | medium two-shot, 35 mm | 187 |
| S08 | …keg party | GARAGE | Party: hero and KegGuy cheer with fists up; Camper and Worker dance. Bulbs, balloons, keg on the party table. Logo box on the shelf. | wide, slow push, 26 mm | 140 |
| S09 | he got a snowmobile | GARAGE | SledGuy presents the blue snowmobile with an open palm; hero steps toward it, both fists up. | wide, push, 28 mm | 156 |
| S10 | which he traded for a trip across Canada | SNOW | Hero walks down the snow trail toward camera (arms swinging), past the parked snowmobile, mountains behind. | low ¾, follows, 30 mm | 172 |
| S11 | (the trip) | SNOW | CU: hero looks out over the mountains, his head following the range, and smiles. No prop: the ticket appears in S12. | CU push, 40 mm f/9 | 109 |
| S12 | the trip for a van | SNOW | Hero gives the ticket to VanGuy; VanGuy gives him the van keys. The blue van is parked behind. | medium two-shot, 35 mm | 187 |
| S13 | (the van) | SNOW | Hero stands at the van's side and opens his left hand toward it (no contact), then turns to camera and grins. The van-side logo is front-on. | medium, push, 28 mm | 117 |
| S14 | the van for a recording contract | STUDIO record | Hero gives the van keys to Exec; Exec gives him the contract (blank line blocks only). | medium two-shot, 35 mm | 187 |
| S15 | which he swapped for a one-year condo rental | STREET | Hero gives the contract to Landlady in front of a house; she gives him the keys. | medium two-shot, 35 mm | 187 |
| S16 | (condo rental) | STREET | Hero lifts the keys in front of him, the brick house behind him. | low push, 30 mm | 109 |
| S17 | He turned that into a day with a rock star | STUDIO bar | Hero hands the keys to Rocker at the bar; the guitar leans on the bar. | medium two-shot, 35 mm | 156 |
| S18 | (rock star) | STUDIO bar | High five: palms meet above head height, then they laugh. | medium, push, 30 mm | 117 |
| S19 | then a band snow globe | STUDIO bar | Rocker hands the snow globe over, cupped from below (generic black-clad band figures, no text). | CU, 40 mm f/9 | 117 |
| S20 | He traded the snow globe… | STUDIO bar | The globe stands on the bar; hero leans in and looks into it, hands relaxed (no contact). | CU over the bar, 40 mm f/9 | 125 |
| S21 | …to a director who promised him a part | STUDIO film | Hero gives the globe to Director; Director gives him the clapperboard (blank slate). Movie camera behind. | medium two-shot, 35 mm | 187 |
| S22 | a part in a movie | STUDIO film | Director cues with the clapper raised; hero acts in the lights, arms open toward the camera. | wide, push, 26 mm | 156 |
| S23 | people all over the world followed… | STREET | Neighbours on the sidewalk: PenLady points down the street, talking; Mayor turns to look. (The newspaper was dropped: the two-hand hold didn't solve cleanly.) | medium, 30 mm | 156 |
| S24 | his story | VOID | Hero CU on the sky stage, holding up the red paperclip in front of his chest, smiling. | CU push, 45 mm f/9 | 109 |
| S25 | waiting to see what he'd trade next | VOID | Explainer: the whole chain of items stands in a row, small to big; the camera tracks along it. No hands. | tracking, 35 mm f/11 | 187 |
| S26 | And exactly one year after he started | STREET | Hero walks along the sidewalk past the blue mailbox toward the houses. | low ¾, 28 mm | 187 |
| S27 | he exchanged his movie role for a house | STREET | Hero gives the clapper to Mayor in front of the house; Mayor gives him the house keys. | medium two-shot, 35 mm | 187 |
| S28 | (for a house) | STREET | House reveal: hero in front of the house, both fists up; the camera cranes up and back. | crane, 24 mm | 140 |
| S29 | famously turning one red paperclip into a home | HOME (as his new home) | Hero walks into the living room, stops, looks around and smiles; the camera pushes in. | push, 28 mm | 203 |

## Logo: DA KRAS FILMS
There are two placements:
1. **White logo on the blue van's side panels**, as decals parented to the van. It is front-on in S13 and visible behind in S12.
2. **Dark logo on a cardboard box** on the garage shelf, seen in S07–S09.

The logo is never on a face, on skin or on a story-beat prop, and no real brands appear. The van's maker badges and text were painted out of its texture.

## Risky shots: the simplest safe staging used
| Risk | Staging |
|---|---|
| Many trades, many hand contacts | Each trade uses one generic swap system. Items move only while a hand holds them, and the hands are driven by item-space grip frames from `grip_object`/`place_hand` (no Child Of offsets). |
| Big items (stove, generator, keg) | Two hands each on the side faces. The previous item rests on the table or ground, so only one item moves. |
| Rock star likeness | A generic Rocker (short hair, black jacket) with no likeness. The snow globe holds generic black-clad figures, with no face paint and no text. |
| Text and brands | No signs, no "one-year lease", no studio name. The contract, newspaper and ticket show only blocks; the clapper is blank. |
| Single-person holds near the body | Fingers always point forward from the hand (wrist inside its limits). The item is re-keyed every frame from the evaluated wrist, so it cannot leave the fingers. |
| Riding the snowmobile or driving the van | Dropped (seat and handlebar contacts). The snowmobile is shown parked and presented, and the van parked with the hero's hand on its side. |
| Item "floating on blue" beat | The items stand still in a row on the sky stage and only the camera moves. Nothing moves by itself. |

## Unsure / for the director
See the P1 message.
