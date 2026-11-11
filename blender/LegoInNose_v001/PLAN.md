# LegoInNose_v001: plan (checkpoint A)

- **Format:** 1080×1920 at 60 fps, frames 1–2310 (38.5 s).
- **Camera:** one camera, `CAM_Film`, on a Catmull-Rom spline through framing keys about every 50–60 frames. It never cuts, never switches and never stops.
- **Script:** ours, 97 words. Each beat starts at its target time, at frame = 1 + round(t × 60).

## Geography: one world, so the camera can physically travel
Everything sits in one scene, and the camera flies between the sets:

```
 [Garden + tree + sky dome]  (seen through the window; seasons change)
        | window
 [LIVING ROOM 5x4 m] --door--> [BEDROOM 3.5x3.5 m] --wall--> [BATHROOM / SHOWER]
        |
   nostril "dive tunnel" (organic, 3 m, hidden except while the camera is inside)
        v
 [STUDIO] at z = -12: a soft cyan-to-white gradient sphere (r = 9 m) holding a 6x-scale
          sagittal CROSS-SECTION of the boy's head (realistic, clean, never gory)
```

- **The dive (room → studio).** The camera pushes macro into the nostril. A flesh-pink mucosa tube carries it at speed: tight, dark, with motion blur. The tube flares open into the studio sphere. One continuous move, as the brief asks: "dive through skin into a cross-section".
- **The return (studio → room).** The camera pulls back out through the same tube in reverse and comes out of the nostril into a macro of his face, then keeps pulling back.
- **The cross-section.** It is built from the boy's MPFB head itself, scaled 6× and cut sagittally with a boolean. Shader cap trick: backfaces render as the flat cut surface (skin, fat and muscle bands). On the cut plane sit modelled inlays for the realistic anatomy:
  - nasal airway with turbinates (glossy pink mucosa)
  - septum cartilage, skull bone (cream), sinus cavity, palate, tongue and brain (soft grey-pink)
  - all in clean explainer colours, studio-lit, with no blood
- **The bricks.** Generic toy bricks: a 2×2 red (bigger) and a 1×2 yellow (smaller). Studs only, no text or logo. Both bricks are copied into the cross-section at matching scale.

## Beat table
f = frame at 60 fps. The camera column gives one framing per ~1 s (C1, C2, … are the spline keys).

| # | t (s) | f | Line | On screen | Camera (continuous) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | "He pushed a Lego piece up his nose, and it got stuck." | Living room, afternoon sun through the window. A 7-year-old boy cross-legged on the rug, a tub of bricks spilled around him, a cat on the sofa, a TV with a cartoon glow (no logo) and dust motes. He picks a red 2×2 brick, inspects it and pushes it up his left nostril (fingers visibly gripping). Wiggles it; it's stuck, eyes cross. At 2.6 s a **cutaway porthole** opens on the side of his nose: inside it the clean cyan-white look shows the brick in the passage. | C1 0.0 low wide over the bricks on the rug, pushing in (28 mm). C2 1.0 orbits to his 3/4 front as the hand rises. C3 2.0 close-up of the hand at the nostril (50 mm). C4 3.0 eases right to profile, framing the porthole. |
| 2 | 4.0 | 241 | "So he pushed a second piece into the same nostril," | His hand dives back into the tub, digs, and plucks the smaller yellow 1×2 brick. The bricks clatter and a few tumble out. | C5 4.0 whip down-left following the hand to the tub (motion blur). C6 5.0 macro on fingers in the bricks. C7 6.0 rises with the hand back up to his face. C8 7.0 tight on the face, two bricks in view. |
| 3 | 7.6 | 457 | "hoping the two would click together so he could pull them both out." | The thought made literal: the yellow brick floats in front of his face beside the stuck red one and snaps onto its studs. A **click flash** (bright glint and sparkle burst) at 8.6 s. He mimes pulling them both out with a hopeful grin. Background in soft bokeh. | C9 7.6 floating macro, lens 70 mm, shallow DOF, orbiting the two bricks. C10 8.6 punch-in on the snap. C11 9.6 pulls out to his hopeful face. |
| 4 | 10.5 | 631 | "It seemed like a clever plan." | He grins proudly, eyebrows up and chest puffed. Then he pushes the yellow brick in after the red one. | C12 10.5 low hero angle on the proud face. C13 11.4 push-in to the nostril. C14 11.9 **dive into the tunnel**. |
| 5 | 12.6 | 757 | "But instead, both pieces got stuck." | Studio cross-section: the two bricks slide up the airway and wedge against the turbinates (squash wobble, mucosa dents). The yellow one slips further up and lodges. At 14.6 s the camera exits the nostril to his **panic**: eyes wide, hands flapping, rocking backward on the rug, the cat bolting off the sofa. | C15 12.6 out of the tunnel into the studio, sweeping across the cut face. C16 13.6 push to the wedge (macro). C17 14.3 back into the tunnel (reverse). C18 14.8 out of the nostril, pulling back. C19 15.4 medium on the panic. |
| 6 | 15.8 | 949 | "His mom pulled out the bigger one," | Mom rushes in from the doorway and kneels on the rug (knees planted), cups his chin, and pulls the red brick out with tweezers, the grip visible. She holds it up; both sag in relief. | C20 15.8 pans right to Mom entering. C21 16.8 low over her shoulder to the tweezers at the nose (macro). C22 17.6 rises on the brick held up and their relief. |
| 7 | 18.1 | 1087 | "never realizing the smaller piece was still lodged deep inside." | The camera dives back in: in the cross-section the small yellow brick, glowing a soft warm yellow (highlighting the named thing), sits hidden high in the passage near the sinus. A slow orbit around it, with the mucosa breathing (subtle pulse). | C23 18.1 push past her shoulder into his nostril. C24 18.6 tunnel. C25 19.3 emerges wide on the cross-section. C26 20.3 slow push in on the glowing brick. C27 21.3 macro orbit. C28 22.1 back into the tunnel. |
| 8 | 22.5 | 1351 | "For 26 years," | Time-lapse in the same living room. The camera orbits a figure seated on the sofa, who ages from boy to teen to 33-year-old man; each swap is hidden as a foreground pillar or lamp crosses the frame. Through the window the tree runs green → orange leaves → bare with snow → green, and the light swings from sun to dusk to blue to sun. A wall clock spins and Mom walks through blurred. | C29 22.5 out of the nostril, pulling back fast. C30 23.3 orbit 120° around the sofa. C31 24.2 orbit continues to the window side. |
| 9 | 24.6 | 1477 | "he battled congestion, asthma and sleep apnea, without knowing why." | (a) 24.6–26.8, **congestion**: the man (33) on the window bench sniffs, blows his nose and drops a tissue into an overflowing tissue box, with tissues scattered on the floor. (b) 26.8–28.6, **asthma**: he shakes an inhaler and inhales; his chest heaves. (c) 28.6–31.1, **sleep apnea**: bedroom at night, moonlight through blinds, alarm clock. He's restless in bed: tosses, gasps, mouth open, throws off the blanket, then sits up confused ("without knowing why"). | C32 24.6 orbit lands on the bench, medium. C33 25.6 close on the sniff. C34 26.6 crane to the inhaler hand. C35 27.6 push to the face. C36 28.6 **flies through the doorway** into the dark bedroom and the light drops to night. C37 29.6 overhead crane down on the bed. C38 30.4 low by the pillow on his gasp. |
| 10 | 31.1 | 1867 | "Then one day, while blowing his nose in the shower," | Morning. The camera passes through the bedroom wall into the bathroom: a tiled shower with frosted-glass partition, falling water streaks (particle-free animated streak meshes), steam (volume) and a rubber duck on the ledge. The man (chest up, framed modestly behind the glass) presses one nostril and blows hard: cheeks puff, eyes squeeze. | C39 31.1 **through the wall**, with a light pop into bright morning. C40 32.1 medium, slow push-in through the steam. C41 33.1 closer on the face. C42 34.0 tight. |
| 11 | 34.6 | 2077 | "the tiny Lego piece suddenly shot out, 26 years later." | **Speed ramp to slow-mo.** The yellow brick shoots out of the nostril with water droplets and lands in his cupped palm. He stares at it (eyes wide, a beat), then breaks into laughing disbelief (head back, shoulders shaking). Last frame: the brick in his palm, his face behind it. | C43 34.6 macro on the nostril (100 mm). The brick's flight is tracked at slow-mo speed (35.0–36.0). C44 36.0 lands in the palm, macro. C45 37.0 pulls back as he laughs. C46 38.5 medium, with the brick still in the palm. |

## Characters (MPFB2 with MakeHuman CC0 assets, `default` rig plus the anim_lib IK controls)
| Name | Phenotype | Clothes | Notes |
|---|---|---|---|
| `Boy` | male, age 0.12 (~7 years) | casualsuit (T-shirt and shorts tint), shoes | short hair |
| `Teen` | age 0.27 (~15 years) | casual | only in the time-lapse |
| `Man` | age 0.56 (~33 years) | casual (bench); a second clothes-less instance in the shower is framed chest-up behind frosted glass | same face family |
| `Mom` | female, age 0.5 | female_casualsuit | ponytail |
| `Cat` | Sketchfab/Objaverse CC-BY cat GLB rigged with `rig_quadruped.py` if one is found quickly; otherwise a sleeping-cat stand-in, flagged | | |

Facial acting:
- The jaw and eye bones animate.
- MakeHuman expression-unit targets are loaded as shape keys where MPFB allows: smile, eyes wide, brow raise, cheek puff.
- If the shape keys don't load, I'll flag it at B.

## Assets and licences
| Asset | Source | Licence |
|---|---|---|
| Humans: base mesh, skins, hair, clothes and expression targets | MakeHuman system assets through MPFB2 | CC0 |
| Furniture and props: Sofa_01, CoffeeTable_01, painted_wooden_bench, old_bed_frame (or GothicBed_01), ClassicNightstand_01, alarm_clock_01, wall_clock, potted_plant_01/02, wooden_bookshelf_worn, throw_pillows_01, Television_01, rubber_duck_toy, tree_small_02 / jacaranda_tree (garden) | Poly Haven | CC0 |
| Textures: wood floor, rug fabric, painted plaster, bathroom tiles | Poly Haven | CC0 |
| HDRI: 2K interior/exterior | Poly Haven | CC0 |
| Generic bricks, tissue box, inhaler, tweezers, tub, cross-section anatomy, dive tunnel, water and steam | Modelled procedurally in script | ours |
| Cat (optional) | find_models.py (Objaverse mirror) | CC-BY, credited |

## Trickiest shots and how I'll do them
1. **The dives (×3), room to studio and back without a cut.**
   - A real tunnel mesh runs from the nostril to the studio. The camera spline goes through it at about 10 m/s with motion blur. `clip_start` is 1 mm.
   - The camera never teleports. The tunnel renders only on the frames the camera is inside it.
   - Check: per-frame camera speed (no spikes) and a still every 0.2 s through each dive.
2. **Cross-section anatomy that's realistic but clean.**
   - The cut is a boolean on the scaled head, with the backface cap shader.
   - The inlays are modelled from the sagittal profile: nasal floor, turbinates, frontal and sphenoid sinus, septum. The colours are pastel and studio-lit; no blood, no gore.
3. **Brick into the nostril.** Scale: the 2×2 brick is about 16 mm wide and the boy's nostril about 9 mm, so it's believable as "jammed in the opening".
   - The brick is parented to the fingertip IK target while held. Then it's parented to the head bone while inside.
   - The audit checks fingertip-to-brick distance under 5 mm while gripped.
4. **The time-lapse aging.** Three characters are swapped while an occluder (a lamp or pillar) crosses the lens. The window seasons and light are keyframed together.
5. **The shower.**
   - Water: animated streak meshes with glossy transmission. Steam: a low-density volume box.
   - Modesty: frosted glass, framing from mid-chest up, and the camera never goes lower than the glass edge on the body.
6. **The slow-mo ejection.** The camera and brick move in real time, but the brick's 0.3 m flight is stretched over 1.0 s. Droplet spheres follow ballistic arcs at slow-mo speed. The palm contact is checked numerically.
7. **Contacts.**
   - The boy sits cross-legged with his pelvis on the rug. Mom's knees and toes are planted.
   - The audit covers hover, sink, hands-to-props, camera inside geometry outside the tunnel, and camera speed.

## Build order
1. `scripts/01_build_humans.py`
2. `scripts/02_build_sets.py`: room, bedroom, bath, garden, studio, tunnel, cross-section
3. `scripts/03_animate.py`: characters, props, FX, lights, camera
4. `scripts/audit.py`
5. `stills.py` and `contact_sheet.py`
6. `beats.json`
7. `package_for_farm.py`, writing to `../LegoInNose_v002/`

## Risks I'm flagging now
- Facial expressions may have to rely on jaw, eyes, head and body acting if the MPFB expression targets don't load in this build.
- Three MPFB characters plus the cross-section head need care to stay under the 150 MB package budget. I'll use subdiv 0 on the background aging stand-ins and 1K textures.
- The cat is optional.
