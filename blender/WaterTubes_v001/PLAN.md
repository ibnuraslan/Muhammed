# WaterTubes — PLAN (checkpoint A)

1080×1920, 60 fps, frames 1–2010 (33.5 s). One camera on one smooth Catmull-Rom spline, no cuts, no camera markers. Beat frame = 1 + round(t × 60).

## Set layout (metres)
- Street runs along X at y = −16 (asphalt, kerbs, verges). Hero house at origin, facing −Y. Front yard between y = −4 and y = −12.
- Neighbours: two each side on our row (x = ±18, ±36), three across the street (y = −30). All are real CC-BY house models (see assets).
- **Tube ring**: a rounded rectangle about 22 × 20 m around the hero house, built from 6 long segments (0.75 m tall, flattened bottom, sagging, wrinkled dark vinyl with seams, ratchet straps and fill valves). Each segment is a curve with a swell shape key so it inflates on cue.
- Flood: brown, murky, foam-streaked water. A moving surge front (displaced mesh) runs down the street from +X; then a level plane rises to 0.55 m everywhere **except inside the ring** (the plane has the ring footprint cut out, so the inside stays dry grass). Splash sprays and foam where it meets the tubes.
- Debris: bins, a floating car, fence panels, branches, a sofa, all bobbing and drifting on the flow.

## Beat table
| # | t | frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | He filled a long tube with water in his front yard | Storm clouds rolling, wind in the trees. The man walks backwards unrolling the flat tube across the lawn; the hose at the valve kicks as water flows, and the tube swells from flat to round along its length. A neighbour across the street hauls bins in. | 0.0 low ground-skim along the tube from the valve; 1.0 rise past the hose nozzle to the man's straining face; 2.0 orbit to his side as he steps back; 3.0 tilt down the swelling tube |
| 2 | 3.7 | 223 | then added more tubes until his entire house was surrounded | Time-lapse feel: segments inflate one after another around the house (staggered swells). The man drags the next tube corner; clouds darken. | 3.7 pull back and up; 4.7 crane over the fence line; 5.7 high three-quarter of the ring closing; 6.7 orbit along the roof ridge, ring complete |
| 3 | 8.3 | 499 | Then floodwater began rushing into the neighbourhood | Brown surge front charges down the street, carrying bins, branches and a floating car that spins. Rain streaks. Neighbours run up their drives. | 8.3 whip-pan down the street to the surge; 9.3 drop low as it rushes at the lens; 10.3 track beside the floating car |
| 4 | 11.8 | 709 | Other homes were damaged | Water pours into a neighbour's open garage and front door; a fence section topples into the flow; a bin tips. | 11.8 dolly past the garage mouth; 12.8 pan with the toppling fence |
| 5 | 13.6 | 817 | but at his house, the thousands of gallons of water inside the tubes | Push to the hero ring; the world falls away to a deep teal-to-navy gradient around one tube segment; its near half cuts away to show the water mass inside, sagging under its own weight, rippling. | 13.6 swing back across the street to the ring; 14.6 push in to the tube skin (macro vinyl, ≤6 frames); 15.6 inside the cross-section, slow orbit; 16.6 lower to ground contact line |
| 6 | 17.2 | 1033 | made them incredibly heavy, too heavy for the flood to push through | Explainer on the same section: a wall of brown water presses on the outer side; orange force arrows push in, a thick downward weight arrow presses the tube into the ground; the tube flattens and holds, the arrows shudder and stop. | 17.2 side-on profile; 18.2 drift to the water side, arrows grow; 19.2 low angle under the weight arrow; 20.2 rise as the gradient opens back to the street |
| 7 | 21.4 | 1285 | The water hit the barrier and flowed around it instead | The flood front slams into the ring, splashes up, curls around the corners and races past; inside, dry grass and the man watching from the porch. | 21.4 over-the-tube looking out at the slam; 22.4 track along the tube with the water curling; 23.4 crane up to see flow splitting around the ring |
| 8 | 24.5 | 1471 | When it was finally over | Water level drops, leaving a mud line, puddles, debris stranded; clouds break, light warms. | 24.5 descend over the receding street; 25.5 skim over mud and stranded bins |
| 9 | 26.4 | 1585 | nearby homes were wrecked | A neighbour's house: brown mud line on the walls, sodden sofa and chairs dragged onto the lawn, the neighbour dragging a chair. | 26.4 dolly along the mud line; 27.4 orbit around the sofa on the lawn |
| 10 | 28.2 | 1693 | but his house stood dry | Inside the ring: green lawn dry, the man on the porch, brows up, jaw open, steps forward amazed and looks around. | 28.2 glide over the tube into the yard; 29.2 push to his amazed face |
| 11 | 30.3 | 1819 | saved by water holding back water | Drone pull-up: a dry green rectangle inside the ring in a brown flooded neighbourhood, sun breaking through. Settle. | 30.3 rise behind him; 31.3 tilt up to top-down; 32.3 slow settle with gentle rotation |

## Assets (all downloaded via pipeline tools)
- Houses (CC-BY, Sketchfab via Objaverse): "2 Story House" by Designed By Jonathan (hero, has a porch); "Suburban House" by mbuannoart; "Suburban Home" by Designed By Jonathan; "Wheeler House" by Sea Land Air; "Surburban Starter House" by novusod; "American style house" by Kishikov.
- Props (CC-BY): Oldsmobile Cutlass '71 by Barbo (floating car), "Trash bin" by tasha.kosaykina, "Wooden Fence" by DmitriyGDS, "Old Sofa" by glezova, "Domestic Hose Unit" by Glowbox 3D, "Simple Mailbox" by Blender3D.
- Poly Haven (CC0): kloofendal_overcast_puresky HDRI (2K), aerial_grass_rock, brown_mud_leaves_01, asphalt_02, rocky_trail textures (1K).
- Humans: MPFB2 / MakeHuman CC0 (hero man, two neighbours). Shirt prints patched out (plain textile).
- Procedural (no real asset exists): the water tubes themselves (vinyl with displacement wrinkles, seams, straps, dirt), floodwater surface, rain, splash particles, explainer arrows.

## Trickiest shots and the plan
1. **Tubes not reading as primitives.** Dark green-black PVC with a flattened contact patch, sag between straps, displacement wrinkles, seam welds, valve caps, wet sheen, mud spatter at the base. Swell via shape key along the length (geometry nodes driven by a moving front) so filling is visible.
2. **Flood that reads as water, not a slab.** Brown absorption/scatter volume shader on a displaced surface, foam streaks from noise masks, a surge front with a curling lip, flowing debris on paths, rain, splash particle bursts at the tube contact. Inside the ring the water plane has a hole so the lawn stays dry.
3. **Cutaway without a cut (beats 5–6).** In-place inner-world shift: a gradient backdrop shell (deep teal to navy) fades in around one tube segment while the camera pushes in; the segment's near half is removed with an animated boolean to show the water inside. Transition through the skin is ≤6 frames of macro vinyl. The backdrop fades out as the camera pulls back to the street for beat 7.
4. **Hands planted on the tube and hose.** IK hands keyed to the tube end and hose nozzle, with a close-up contact pass before stills.
5. **Life every beat.** Neighbours moving, trees and grass in wind, rain, rolling clouds, debris drifting, light changing from storm to clearing.

## Deviations noted
- The film brief says Git LFS / 150 MB, but the Batch 2 rules and the launch message say **under 95 MB, normal git, no LFS**. I am following the 95 MB / no-LFS rule.
- beats.json is written from the target times above.
