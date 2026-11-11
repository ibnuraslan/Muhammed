# HeadsetBullet_v001 — plan (checkpoint A)

1080×1920, 60 fps, frames 1–1500 (25.0 s). One camera `CAM_Film`, one continuous Catmull-Rom spline move, no cuts, a new framing every ~1 s.
Our own 69-word script; no VO yet, built to the brief's target times; `beats.json` written for `retime_to_vo.py`.

## Set layout (one continuous world)
- Suburban street → front lawn → single-storey house with clay roof tiles (Poly Haven), white plaster walls, a front window at x=-0.6, z≈1.3.
- Behind that window is **his room** (4.2 × 3.6 m, built in-scene, so the camera can fly straight through the shattered window into it): plank floor, painted walls, posters (no text), bookshelf, bed corner, desk on the far wall with a big monitor (generic game image, no UI text), RGB keyboard, mouse, gaming chair.
- He sits with his back to the window, slightly turned, so the bullet line from the window reaches the **left ear cup from behind-left**. Ricochet goes off to his right-front into the **side wall** (plaster chips, dust puff, a hole he looks at in beat 10).

## Beat table (frame = 1 + 60·t)
| # | t (s) | frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | A bullet was fired toward the house | Sunny suburban street; a copper bullet streaks in slow motion over the lawn (no shooter). Sprinkler, a bird lifts off the fence, tree leaves sway, parked car, mailbox. | Starts low beside the bullet at street level → chase from behind/right → rises over the fence as the house fills frame. |
| 2 | 2.2 | 133 | smashed through the window | Bullet meets the window: glass cracks radially, then a slow shard cloud bursts inward, curtain flutters. | Pushes in behind the bullet, flies *through* the hole in the glass with the shards around the lens. |
| 3 | 4.0 | 241 | headed straight for his head | Inside: the teen at the desk, back to us, monitor glowing; bullet crawls toward the back of his head; shards still drifting. | Follow-cam just above/behind the bullet, the head growing in frame; slight downward drift. |
| 4 | 5.9 | 355 | gaming at his desk, wearing a headset | Bullet almost frozen. He plays: fingers on WASD, mouse flicks, shoulders lean, monitor light flickers on his face, a soda can and snack on the desk, game lights on the wall. | 3.6 s orbit: behind → over right shoulder (hands on keyboard+mouse) → low front past the monitor edge (face lit by the screen, headset) → round to his left side where the bullet is. |
| 5 | 9.5 | 571 | instead of piercing his skull | Extreme slow motion; bullet 20 cm → 3 cm from the left ear cup, spinning; air ripple. | Slow push to macro along the bullet, side-on, ear cup and temple in frame. |
| 6 | 11.6 | 697 | the bullet hit the headset first | Impact: the plastic shell cracks, fragments and dust fly, the head jolts a few degrees with follow-through. | Macro holds the impact point, small shake, slight pull-out to show the head jolt. |
| 7 | 13.9 | 835 | thick padding and the metal frame inside | Cutaway of the cup (animated boolean): foam cushion layers and the steel band/frame; the bullet compresses the foam, hits the metal and tilts. Cyan studio rim light comes up for the explainer moment. | Dives into the cutaway plane, slow arc around the bullet inside the cup. |
| 8 | 15.8 | 949 | deflected the bullet, sending it safely away | Bullet ricochets off at an angle, sparks; flies across the room in slow-mo, speed ramps up and thuds into the side wall: plaster chips + dust puff + hole. | Pull back out of the cup → whip-pan following the bullet to the wall → push in on the hole, then swing back to him. |
| 9 | 19.4 | 1165 | pulled off the broken headset | He flinches, grabs both cups (visible grasp), rips the headset off, chair rolls back; turns it in his hands: cracked cup, bent band. | Medium side → close on his hands turning the headset (cracked cup toward lens). |
| 10 | 21.9 | 1315 | realized it had just saved his life | Close-up stunned face (brows up, jaw drop, breathing), he slowly turns to look at the hole in the wall. Settle. | Close-up on face → rack focus + drift to the hole over his shoulder, slow settle. |

## Assets and licences
| Asset | Source | Licence |
|---|---|---|
| Teen (body, rig, skin, short hair, casual clothes, shoes, eyes, brows) | MakeHuman system assets via MPFB2 | CC0 |
| HDRI sunny sky (e.g. kloofendal_48d_partly_cloudy_puresky), roof tiles, plaster, planks, grass, asphalt, bricks | Poly Haven | CC0 |
| Shrubs, potted plant, tree_small_02, desk lamp, bookshelf (wooden_bookshelf_worn) | Poly Haven | CC0 |
| Gaming chair, monitor, keyboard+mouse (logos checked/removed) | Sketchfab via Objaverse | CC BY 4.0 (credited) |
| **Built in-scene** (no download): the bullet (plain copper projectile only, no cartridge or weapon detail), the headset (shell, foam, metal frame, so it can crack and be cut away), the house shell + room, window glass + shards, sparks, dust | our scripts | ours |

## Trickiest shots and how
1. **Headset on the head (clipping rule):** our own headset built to the MPFB head's measured width, Child Of → `head` bone, cushion offset 4 mm out from the skin with a shrinkwrap check; hair under the band hidden. At beat 9 the Child Of influence is handed to the hands (two keyed Child Of constraints) after the fingers close on the cups.
2. **Fly-through window:** glass fractured by script (Voronoi-ish radial shards); shards get keyed ballistic paths spreading from the hole; the camera path threads the opening with the clip start at 3 cm.
3. **Cup cutaway:** boolean DIFFERENCE with a keyed cutter box sliding in on shell + foam; foam compression via a keyed simple-deform/scale, metal frame stays.
4. **Ricochet + wall hit:** keyed bullet path with a speed ramp; spark streaks (emissive stretched quads); plaster chip debris; a hole decal that stays for beat 10.
5. **Hands:** keyboard/mouse contact uses IK hands keyed onto measured key-top/mouse surfaces; headset grasp keyed on cup surfaces; checked with a BVH penetration audit.
6. **One camera** for 25 s: Catmull-Rom through ~28 framings, plus a whip-pan accent at beat 8.

## Risks
- MPFB face has no expression rig in our setup: stunned face done with jaw/eyelid/brow bones where present, plus head/neck acting.
- Downloaded models may carry logos; we'll overwrite their textures if so.
