# StanleyCup_v001 — PLAN (checkpoint A)

Connect04 · branch `claude/connect04-tumbler-saves-life` · 1080×1920 · 60 fps · frames 1–1530 (25.5 s) · one camera `CAM_Film`, no cuts.
Frame = 1 + round(t × 60). No VO yet: built to the brief's target times; `beats.json` is written for `retime_to_vo.py`.

## Story-time
Everything after the wall is **extreme slow motion**: the bullet crosses ~3.2 m of living room in ~11.7 s.
Before the wall it is "fast slow-mo" (≈ 9 m in 2.3 s) so beat 1 still reads as a shot being fired. Humans act at ~1/8 speed during beats 4–6
(blinks, eye-widen, his reach), back to real time after the bullet drops (beats 7–8).

## Beat table (one framing per ~1 s; all framings are keys on one Catmull-Rom camera spline, velocity never stops)
| # | t (s) / frame | Line | On screen | Camera framings |
|---|---|---|---|---|
| 1 | 0.0 / 1 | A bullet was fired at the house | Suburban street at dusk: clapboard house with lit windows, porch light, neighbours' houses, trees swaying, street lamp flickering on, leaves blowing, a cat on the porch rail bolts. A bullet with a faint heat-shimmer trail streaks in from off-screen left (no shooter). | 0.0 low wide street-level, bullet enters frame-left close to lens · 1.0 camera whips in behind it, bullet-cam chase, house grows · 2.0 tight over the bullet's shoulder, siding fills frame |
| 2 | 2.3 / 139 | tore straight through the wall | Bullet punches the siding: board splinters, paint chips, dust puff, then the cross-section of the wall (siding → sheathing → insulation fluff → stud gap → drywall) as the camera follows it through the hole; drywall bursts into the room in a gypsum dust cone. | 2.3 macro on impact, splinters past lens · 3.0 inside the wall cavity, lit by light leaking through the hole · 4.0 burst out of the drywall with the dust |
| 3 | 4.5 / 271 | Inside, a woman and her fiancé | Modern living room at evening: dining table, the couple seated opposite each other mid-conversation (he gestures, she laughs and lifts her glass), sofa, shelf, lamp, plants, TV glow, pendant light. Picture frame on the wall rattles from the hole. | 4.5 wide over the bullet, room revealed · 5.5 camera overtakes and skims past the bullet, low over the table edge toward the couple |
| 4 | 6.5 / 391 | froze… raced straight toward her | Extreme slow-mo. Her eyes widen, brows up, shoulders lift; he turns his head and reaches his hand toward her across the table; dust motes hang; the bullet crawls with a shimmer wake, spinning. | 6.5 close on her face (bullet out of focus fg) · 7.5 orbit to his side, his reaching hand · 8.5 bullet-level side view, bullet fg → her bg · 9.5 low angle along the bullet's line, tumbler appears between them |
| 5 | 10.1 / 607 | her trusty tumbler, full of ice water | Rack focus from the bullet to a large insulated steel tumbler (handle, lid, straw; generic, no logo) on the table between them. Condensation beads run down, ice cubes clink and turn behind the clear lid window, straw trembles. | 10.1 rack focus bullet → tumbler · 11 slow orbit, condensation macro · 12 top-down into lid/straw, ice · 13 steel reflection shows the couple · 14 pull back: bullet, tumbler, woman aligned · 15 lens-axis down the bullet path · 16 tight on the contact point |
| 6 | 16.2 / 973 | the bullet slammed into the cup | Macro impact: steel dents inward (shape key, squash), spark burst (particles-free instanced spark streaks, emissive), droplets fly off the condensation, the cup skids 2 cm. The camera dives through the steel into a clean **cutaway** of the double wall: water ripple rings and ice bobbing inside. Bullet nose mushrooms. | 16.2 macro impact · 17 orbit around sparks · 18 dive into the cutaway, ripples · 19 out again; bullet rebounds, flattened · 20 wider: she flinches back, he grabs her wrist · 21 bullet falls off |
| 7 | 21.4 / 1285 | dropped harmlessly to the floor | Real-time again. The deformed bullet tumbles off the table edge, bounces twice on the wood floor, rolls and settles by the chair leg. Couple both jolt back. | 21.4 follow it over the edge · 22.4 floor-level skim, bounce · 23.2 settle close-up |
| 8 | 23.6 / 1417 | saving her life | Crane up from the bullet to the woman, shaken, hand on her chest, the other hand gripping the dented tumbler's handle and lifting it; he comes round and holds her shoulders. | 23.6 crane up past the table edge · 24.6 medium on her holding the tumbler, dent toward lens · 25.5 end |

## Camera path (one spline)
Street (x≈-10 m, 0.4 m high) → behind bullet → through the wall hole at the dining-room side wall → room → orbit tumbler → dive into cutaway (a cutaway duplicate of the cup sits in place; the camera passes through the steel surface so it's a fly-through, not a cut) → floor → crane up. Lens animates 24–85 mm (macro beats use 60–85 mm with shallow DOF and keyed focus distance for the rack focus).

## Assets
| Asset | Source | Licence |
|---|---|---|
| Woman, fiancé (bodies, rig, skins, hair, clothes, eyes) | MakeHuman system assets via MPFB2 | CC0 |
| Dusk HDRI, wood floor, plaster, siding/wood, brick/asphalt textures | Poly Haven | CC0 |
| Dining table, dining chairs, sofa, shelf, plant, lamp, picture frames, coffee table | Poly Haven models | CC0 |
| House exterior (clapboard, windows, porch, roof), wall cross-section, neighbour houses | built procedurally in script | ours |
| Tumbler (lathe profile, handle, lid, straw, ice, water, condensation), bullet, sparks, dust, splinters | built procedurally in script | ours |
| Trees / bushes outside | Poly Haven or Objaverse CC-BY (credited) | CC0 / CC-BY |

## Hardest shots and how
1. **Wall fly-through (beat 2):** prefractured siding boards + drywall chunks near the hole, keyed rigid flight (no sim, so it packs clean); wall built as real layered cross-section so the camera passes through a real hole; a boolean-free hole mesh (inset hole modelled in each layer).
2. **Dent + sparks (beat 6):** tumbler body gets a dent shape key keyed at impact; sparks are ~60 instanced emissive streaks with keyed ballistic paths; condensation droplets fly off.
3. **Cutaway / ripples:** duplicate cut-in-half tumbler with a water surface plane carrying a keyed displacement (radial wave texture with animated phase); the camera passes through the steel at the cut seam.
4. **Seated humans:** MPFB rig with IK; hips locked on the chair seats (numeric audit for seat/table/hand penetration). Hands visibly grip the tumbler handle in beat 8 before it lifts (cup parented to the hand from the grip frame).
5. **Facial acting (freeze):** MPFB default rig eyelid/jaw bones + head/shoulder lift; if facial bones are too limited, shape keys from MPFB expressions.

## Risks to flag
- Slow-mo humans must not read as a held pose: continuous micro-motion (breath, hair, blink, the reach) through beats 4–6.
- Render time is unknown until the scene is built; target ≤ 150 MB .blend.
