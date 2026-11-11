# CaveRescue: plan (checkpoint A)

Connect23. Branch `claude/connect23-cave-rescue`. 1080×1920, 60 fps, frames 1–3090 (51.5 s). Cycles CPU.
Script: ours, 114 words (`briefs/23_CaveRescue.md`). Beat frame = 1 + round(t × 60).

## World layout (one scene, one camera)
All sets sit in one scene, and one camera travels through them on a Catmull-Rom spline (pattern from `goat_rescue2_v001/03b`).
- **S1 Hillside + cave mouth** (origin): wet jungle slope, a limestone mouth facing −Y. It is used in beats 1–2 and 13–14 (rain, then sun).
- **S2 Entrance tunnel**: a displaced rock tube running +Y into the hill from the mouth, so the camera physically follows the boys inside. It floods in beat 2.
- **S3 Mountain cross-section**: a 1:100 cutaway mountain (x = −400). It has the route tube, sumps (low U-bends), a ledge chamber at the far end, and a glowing route line (an emissive curve grown with bevel-factor). The water planes in the sumps rise in beat 4, and the route segments below the waterline turn blue.
- **S4 Chamber**: a full-scale muddy ledge above a black pool (x = +400). It is used in beats 5 and 8–11.
- **S5 Flooded passage**: physically connected under S4's pool. It's a narrow rock squeeze with a guide rope, silt volume and particles, and zero-visibility murk. The camera dives from the chamber into the pool and through here. Used in beats 6, 7 and 12a.

**Moving between scales.** S2→S3, S3→S4, S5→S3 and S3→S2 are fly-throughs into solid rock. The camera keeps its velocity into the rock, the frame goes to rock texture and then black for 3–4 frames, and the spline jumps while it's inside the rock. This is the "dive through skin into a cross-section" move. It's the same trick as goat_rescue2's sky tilt: there's no camera switch and no marker, just one camera object.

## Beat table
| # | t (s) / frame | Line | On screen | Camera (~1 framing per s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | In 2018, a group of boys and their soccer coach were exploring a cave in Thailand | 6 boys (11–16) pushing bikes and a young coach walk up the wet jungle slope. They lean the bikes at the mouth, switch on torches and walk in. Mist, ferns sway, birds. | High crane over the trees → low dolly behind the bikes' wheels → over-the-shoulder of the coach → follow them through the mouth (dark swallows the frame edges) |
| 2 | 4.9 / 295 | when heavy rain suddenly flooded the tunnels, trapping them inside. | The camera whip-pans back to the mouth: monsoon rain, a brown torrent pours over the lip. Back inside, water surges along the floor and the boys run deeper, torch beams swinging. | Whip back toward the mouth (rain) → whip forward, a low skim over the rising water chasing the boys' legs |
| 3 | 9.6 / 577 | They were more than two miles in, | Pull back sideways through the tunnel wall (rock) and out of the cut face of the huge mountain cross-section. The glowing route line grows from the entrance to a tiny ledge chamber deep inside. | A fast pull-back through rock → wide of the whole mountain, then a lateral track following the line's growing tip |
| 4 | 12.1 / 727 | and the narrow passages leading out were now completely underwater. | The cross-section floods: murky water fills each low sump in turn, and the route line under the water turns blue. | Drift along the route from the entrance side toward the chamber, the water rising in frame |
| 5 | 16.7 / 1003 | After 10 days, divers finally found them, | Push into the tiny chamber (rock, then dark) and emerge in S4: the boys huddled thin and muddy on the ledge. Bubbles, then a diver's head torch breaks the pool surface; the boys raise their hands and squint into the beam. | Push-in from macro of the cross-section → reveal over the huddled boys → a low angle at the waterline as the diver surfaces → reverse over the diver's shoulder onto the squinting faces |
| 6 | 20.2 / 1213 | but the flooded tunnels were so dangerous | Dive into the pool: divers squeeze one at a time through a tiny flooded gap, hand over hand along the guide rope, with silt billowing and torch cones in murk. | Down through the surface → tight on the gloved hand on the rope → an under-the-gap angle as a tank scrapes through |
| 7 | 24.8 / 1489 | that even a skilled diver died during the operation. | A lone diver swims away into the dark water. His light dims and fades out. Silence beat: silt settles, the rope sways, there's no body. | Slow drift, wide and respectful; the light recedes, then a very slow push into darkness with no cut |
| 8 | 28.5 / 1711 | Swimming the boys out themselves seemed impossible. | The camera rises up out of the black water and finds a boy at the ledge edge looking down into it. Close on his frightened face lit by a torch, and the dark water reflected. | Up through the surface (the water line wipes the frame) → a low angle up at the boy → push to a close-up of his eyes |
| 9 | 33.6 / 2017 | So rescuers chose a last resort. | The rescue team kneels around the boys with gear bags, tanks and masks. They nod and plan. | Orbit around the kneeling group |
| 10 | 35.9 / 2155 | They sedated the boys, | A medic swabs, then gives a careful injection in the upper arm; the boy's eyes close, calm. | A tight orbit to the arm (insert), then up to the eyes closing |
| 11 | 38.8 / 2329 | fitted them with full-face diving masks, | A full-face mask is pressed on, straps pulled behind the head, and bubbles start at the regulator. | Close on the mask seal at the cheek, then a pull to medium as the diver lifts him |
| 12 | 40.1 / 2407 | and carried their unconscious bodies through the tunnels, one by one. | The diver tows the boy, strapped in a stretcher-like harness, through the flooded passage, with the camera travelling alongside. Then we pull out through rock into the cross-section: light dots move along the route line one by one, handed along a chain of divers. | Side-tracking travel underwater → pull back through rock → wide cross-section tracking the dots toward the entrance |
| 13 | 45.4 / 2725 | All 12 boys and their coach made it out alive, | Push into the cross-section's entrance → emerge in S2 looking out at the bright mouth → fly out into daylight: stretchers carried out, a crowd cheering, ambulances, a helicopter landing, flashing lights. | Fly out through the mouth, then a low dolly beside a stretcher, then a rise over the crowd |
| 14 | 48.8 / 2929 | after 18 days underground. | Crane up out of the jungle as the clouds part and god rays break over the green hills. Settle. | Crane up and tilt to the horizon; it eases out at frame 3090 |

Beat frames: 1, 295, 577, 727, 1003, 1213, 1489, 1711, 2017, 2155, 2329, 2407, 2725, 2929; end 3090. These go in `beats.json`.

## Characters (MPFB2 + MakeHuman CC0)
- **Boys**: 5 unique (age 0.19–0.27, mostly asian skin, short hair, casualsuit/sportsuit, tinted jerseys with no logos). There are more copies for the group of 12, with linked mesh data and their own actions.
- **Coach**: a young adult in a casualsuit.
- **Divers**: 3 adults in a black-tinted sportsuit (wetsuit), with a tank, BCD, fins, a head torch and mask as props. Head items go on the head bone with Child Of plus a small offset (clipping-check rule).
- **Medic**: one of the divers, in a lighter top.
- **Crowd / rescuers in beat 13**: re-dressed copies of the above, in rain jackets and helmets.
- **Rig**: MPFB default + the IK controls from `pipeline/anim_lib.make_human_ctrl`. `Human.walk` handles the walks, with planted feet on `ground_z` ray-cast against the set floor. Swim, kneel, huddle and the injection are poses with FK and IK hands.

## Assets (all CC0 or made by us)
- **Poly Haven (CC0)**: island_tree_01/02, fern_02, shrub_01/02, rock_face_01, boulder_01, rock_moss_set_01; textures rock_wall_08, brown_mud_02, forest_ground_04, rocky_trail, aerial_rocks_02; HDRIs forest_slope and kloofendal_overcast (2K).
- **Procedural (ours)**: cave tubes, cross-section mountain, bikes, tanks, masks, torches, stretcher, ambulances (plain white with red and blue lights, no text), a helicopter (plain, no markings), rain, silt, bubbles, the route line.
- Nothing with text, logos or real likeness.

## Trickiest shots and how
1. **Scale changes without cuts**: the rock fly-through jumps above. Verify each one frame by frame in the 0.2 s sheets, and make sure no frame shows both sides.
2. **Underwater look**: a world volume in an "Underwater" box (absorption plus scatter), a silt particle cloud, torch cones as spot lights with volume, and a rippled water surface plane with transmission. The camera crossing the surface is a water-line wipe.
3. **Diver light fade (beat 7)**: a spot light plus emissive lamp on a diver who swims off along a curve. Energy keys go 400→0 over 2.5 s, and the silhouette is lost to the murk before he's gone. There's no body.
4. **Huddled boys and kneeling team**: seated and kneeling poses with feet and knees planted on the ledge via `ground_z`. A penetration audit covers body against ledge and between characters.
5. **Mask fit**: the full-face mask is a modelled oval with a strap ring. It's Child Of to the boy's head bone, and the diver's IK hands are keyed on the mask rim and strap.
6. **12 boys, one by one**: in the cross-section, 13 emissive dots travel the route curve with staggered starts (Follow Path offsets). Small diver dots sit at the chain points.

## Schedule (UTC, from the launch message)
A ~19:55 · B 23:15 (1 still/s) · C 00:45 (0.2 s sheets + audit, incl. BVH penetration count) · D 01:30 (package in `CaveRescue_v002/`).
