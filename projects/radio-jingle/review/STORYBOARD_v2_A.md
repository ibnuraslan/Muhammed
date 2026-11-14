# Radio Jingle, part A (Cold Open, Ch1, Ch2): storyboard v2

Everything is realistic Cycles in look v5: real 3D sets and objects, with no flat, vector or illustrated graphics.
The flat paper-map test was dropped before review.

Rule 7 is applied both ways:
- No hand-only frames: every action shows the person (head, shoulders and arm).
- No object acts by itself: evidence objects lie still, and only the camera and light move. Clock hands, smoke and flicker are the natural exceptions.

Sheet: `review/STORYBOARD_v2_A.jpg` (before | after for every changed shot).
Motion previews (about 480p, 12 fps, low samples): `review/previews_v2/A_*.mp4`.

## Changed shots

| # | Shot | Old idea | New idea | Why it's stronger |
|---|---|---|---|---|
| Ch1 4B | house **lapse** | From behind, the mother hangs up and looks at the clock | Close on the hall clock in time-lapse from 7:20 to 7:50, the pendulum a blur. The last sun through the door glass lays a window-shaped patch with its cross bar on the wall; it climbs over the clock and leaves. The phone below stays silent. | It turns "ten minutes ... half an hour later" into time you can see passing. No one is in the hall, which is the dread. |
| Ch1 7A | aerial **meet** | Wide and high: two small figures meet at the bend | A top-down drone at blue hour over the dark wood. The pale path curves through it. Two real figures (the father and the uncle), each with a torch pool, walk toward each other from both ends and meet at the bend. The camera sinks and turns slowly. | The geography is clear in one image: two villages, one path, a gap in the middle. It is real, with no map graphics. |
| Ch1 8B | aerial **search** | Firefighters with lanterns walk the reed edge | A top-down drone at night. Torches come on along the path, and two thirds of them leave it and fan out into the black wood. Village windows are lit, and a blue light pulses at the end of the path. | The scale of the search ("police, firefighters, and neighbors") reads as dozens of lights. A count made physical. |
| Ch1 9-10 | path **brush_long** (one 22 s take) | Four shots: dog_low, dog_front, brush_find, brush_ring | **Chapter 1 hero long take**, one unbroken move. We follow behind the handler as the dog, a dark shape only, pulls him off the path into the wood. His torch sweeps, slows and stops on the red bicycle in the ferns. The camera goes on past his shoulder to the bicycle while the other torches come through the trees and close round it. Then it cranes up. | It holds the emotional peak in real time and never cuts away. It replaces four literal inserts. |
| Ch1 17A | void **letter** | Slow overhead push onto the letter on the kitchen table | The cut-out letter alone on black, under one hard top light. Crooked newspaper letters read "2 MILLIONEN / GEBRAUCHTE / HUNDERTER". A slow top-down push. | Evidence presented as a hero object, the way it would be shown in court. It recurs in B's half. |
| Ch1 20A | void **money** | An officer lays bundles into the open suitcase | Two hundred bundles of used hundred-mark notes (100 notes each, 2 million) as one block on black. Low push and turn. | The ransom as a physical quantity you can weigh by eye. The father then closes the case (latch, reframed to show him). |
| Ch2 5B | void **bolts** | From behind, an officer works a bolt with a crowbar | Seven barrel bolts shot home along the rough planked lid, on black. A low macro track along the row, one bolt after another. | The "seven" is counted out on screen. It is the shut-in detail without showing anyone in danger. |
| Ch2 8A | void **items** | A push across the shelf in the box | What was in the box laid out as evidence on black: water, orange soda, chocolate, books and the portable radio. A slow overhead track. | The script's list is shown item by item on the words. The radio is the recurring object (box, then B's chain). |
| Ch2 10A | void **span** | Two experts at a table of files | A real wall clock on black. Its hands race from half an hour to five hours (7:45 to 12:15) while the second hand sweeps. Slow push to the face. | "Between thirty minutes and five hours" becomes a span of time on a clock face, not two people at a desk. |
| Ch2 13 | woods **night_long** (one 20 s take, "Court reconstruction" label) | A lone torch moving through the trees, then it goes out | **Chapter 2 hero long take.** At night over the five little spruces, a faceless dark figure with a torch comes through the mist between the trunks. He stops at the clearing's edge with his beam on the spruces. The torch goes out, and in the dark he turns away. | Fixes rule 7 (no torch moving by itself). The court's inference is shown as a silhouette, never a face. |
| Ch1 20B | house **latch** (reframed) | The officer's head was cut at the top of the frame | Wider and lower: the whole person closes and fastens the case. | Rule 7. |

Kept unchanged, already person-driven and approved: the Cold Open, the piano, the gate and lane, the rides, the dial, the uncle and father walks, father_call, night_line, the brother, the bench, the heli and divers, the kitchen radio and window, the ring and listen, the post, read, thread and door, call_left and toys, the Fiat, silent and stairs. Also kept: Ch2 line, tape, rods, hit, converge, dig, sweep, lid, lift, cap, crane, cable, radio, pipe, smoke, door, co2, spr_orbit, spr_low, pull and bend_long.

Shot-length rhythm: each chapter now has one long hero take (Ch1 brush_long, Ch2 night_long) among 3-5 s inserts, as in the references.

## New code

- `rj_case.py` (shared with B): `void_spot()` (black world, one hard top light, glossy floor fading out), a red thread, and a reveal line.
- `sc_void.py`: the object-on-black evidence set (letter, money, bolts, items, span).
- `sc_aerial.py`: about 1 km of the real north shore (terrain, mixed spruce and birch wood, lake, two villages, the path). The moves meet and search are top-down drones at blue hour and at night.
- `sc_house.lapse`, `sc_path.brush_long`, `sc_woods.night_long`. `rj.ROLES["stranger"]` is a dark silhouette only.
- `chapters.py`: running order updated (Ch1 41 shots, Ch2 27 shots).
