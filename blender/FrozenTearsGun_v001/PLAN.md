# FrozenTearsGun_v001: plan (checkpoint A)

35.0 s, 1080×1920, 60 fps, frames 1–2100. One camera `CAM_Film` on one continuous spline (Catmull-Rom through ~36 keyed framings, ~1 per second, continuous velocity). No cuts, no camera markers, no on-screen text.

## Sets (all real-world except the device cutaways)
| Set | Where in world | Used by beats |
|---|---|---|
| **Workshop** (night, warm desk lamp + cool window): workbench, pegboard with tools, vice, drill press, shelves of jars/brass stock, sketches pinned, stool, concrete floor, plaster/brick wall | origin | 1–8, 12–13 |
| **Explainer pocket**: cyan→white gradient cyclorama + softboxes, built *around the gun* at macro scale. World/backdrop opacity keyed so the workshop dissolves into the gradient as the camera dives into the glass chamber, and back out | at the gun | 3, 5, 6, 7 (cutaway) |
| **Office** (memory, cooler daylight, desaturated grade): desk, monitor (blank), bookshelf, window blinds, plant, chairs, papers | x = +12 m, behind the workshop's back wall | 9–11 |

## Characters (MPFB2, CC0 MakeHuman assets, generic)
- **Inventor**: woman, 20s, ponytail, casual suit (tinted denim-blue top), young skin. IK hands/feet (`anim_lib.make_human_ctrl`). Crying face from the default rig's face bones (brows `levator`, lids `orbicularis`, mouth corners `risorius/oris`, jaw), plus tears, sniff/shoulder shake.
- **Mentor**: man, ~60, bald, elegant suit (shirt + tie, no logos), old skin. Lecture gestures, startled flinch, final arms-out brace with wince-smile.
- Characters teleport between sets only while the camera is inside a transition (blur / fly-through), never on screen.

## Hero props (procedural, built in script, no brand marks)
- **Monocle-funnel**: brass cone under her left eye on a thin arm hooked over the ear; clear silicone tube (curve + bevel, hooked to head bone and gun inlet) runs down the cheek and neck to the gun.
- **Tear gun**: brass + glass pistol: glass reservoir chamber on top, valve wheel, plain grey CO2 cylinder (no text), cut-glass barrel window showing the spring and plunger, trigger, wooden grip.
- **Tears**: animated drops (well on lower lid → roll down cheek → into funnel → along tube → drip into chamber). Water → ice material blend, frost crystal sprites growing on the chamber wall.
- **Gas**: white puffs (volume-scatter blobs, keyed scale/density) venting from the canister nozzle.
- **Spring**: helix mesh, keyed compress/release with overshoot.
- **Pellets**: ~12 ice balls + glints (small emission stars) in slow motion out of the barrel.

## Beat table (target starts; ~1 framing per second; camera moves continuously)
| # | t (s) | frame | Line | On screen | Camera |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | "As she cries," | Close on her face at the bench, lip trembling, brows up, tear swelling on the lower lid; brass funnel under the eye glints in lamp light; workshop alive behind (lamp, steam from mug, pegboard) | starts tight 3/4 on face, slow push + slight orbit right (0–1 s), drift down toward the cheek (1–2 s) |
| 2 | 2.3 | 139 | "her tears roll down into a tube" | Tear runs down cheek into funnel, enters clear tube, slides down the tube along her neck | macro; camera locks onto the drop and rides alongside the tube (2.3–4.5 s), two framing changes as the tube bends over the collarbone |
| 3 | 4.5 | 271 | "and drop into the gun." | Drop exits tube into the glass chamber; plink + ripple; more drops already pooled | camera follows into the glass; backdrop dissolves to cyan studio gradient (cutaway); slight crane up over the chamber |
| 4 | 5.8 | 349 | "When she turns the valve," | Her fingers grip and turn the brass valve wheel (grasp visible first) | pull back and orbit to reveal hand + gun on the cyan backdrop |
| 5 | 7.3 | 439 | "a CO2 canister releases gas" | Plain canister; valve opens; white gas jets into the chamber, swirls | orbit down past the canister nozzle (7.3–8.5), push along the gas jet into the chamber (8.5–10) |
| 6 | 10.1 | 607 | "freezing the tears into tiny balls of ice." | Drops frost over from the edge, turn white-blue, shrink into round pellets; frost crystals creep over the glass | extreme macro on one drop, slow orbit 90°, rack focus to the crystals growing on the glass, rise to see the full chamber of pellets |
| 7 | 13.4 | 805 | "And when the trigger is pulled," | Finger squeezes trigger; cutaway: spring compresses, latch drops, spring releases | track along the gun body from grip to barrel window, spring in centre |
| 8 | 15.0 | 901 | "a spring fires the frozen tears just like a real gun." | Slow-mo: pellets burst from the muzzle, frost puff, glints; backdrop returns to the workshop; she lowers the gun, still teary | whip-follow with the lead pellet out of the barrel, rising, the room smearing past in a slow speed ramp |
| 9 | 18.7 | 1123 | "You see, a while back, she had a stressful meeting with her mentor" | Lead pellet flies into the window/glass of a framed photo → focus blur → the office forms; mentor (bald, 60) behind desk lecturing, jabbing finger, papers; she sits across, shrinking | camera flies with pellet through a full-defocus blur (fly-through), pulls focus onto the office, over-the-shoulder of her, then arcs to his side |
| 10 | 22.4 | 1345 | "and burst into tears." | She breaks down: hands to face, shoulders shaking, tears; mentor stops mid-gesture | push in on her from the side/front, low angle |
| 11 | 25.5 | 1531 | "She was so upset, she wished she could shoot him with her tears." | A translucent thought-bubble blooms from her head; inside it (same set, dreamy grade, bubble rim around frame) tiny tear projectiles pelt the startled mentor who flinches/ducks behind his folder; bubble pops | rise up into the bubble over her head, then glide across the desk toward the mentor through the pelting tears |
| 12 | 28.3 | 1699 | "So she designed this tear gun." | Workshop time-lapse: lamp/window light sweeping, she sketches the gun (paper sketch, no text), files a brass part at the vice with sparks, parts appear on the bench, she assembles | pop through the bubble into the workshop; quick 3/4 orbit around the bench (3 framings in ~3 s) |
| 13 | 31.2 | 1873 | "And when it was finished, her mentor agreed to let her shoot him." | She lifts the finished gun; mentor in the workshop doorway stands arms out, braces, wince + smile; she fires; ice puff and sparkles hit his shirt; he laughs, she laughs through tears. Settle | pull back to a two-shot over her shoulder, push past the gun to the impact on his shirt, settle drifting back for the final frame |

`beats.json` will be written from the table above (frame = 1 + round(t × 60)).

## Assets and licences
- MPFB2 / MakeHuman system assets: CC0 (bodies, clothes, hair, skins).
- Poly Haven (CC0): studio HDRI (e.g. `studio_small_09`), interior HDRI for window light, textures: concrete floor, plaster/brick wall, wood planks/bench, brass/metal plates as needed. Possibly Poly Haven models (e.g. desk lamp, chairs, books, potted plant, tools) where available.
- Sketchfab via Objaverse (CC-BY, credited in `CREDITS.md`): office desk, office chair, bookshelf, drill press/vice, pegboard tools, as needed. Each checked on the thumbnail sheet first.
- Hero props (gun, funnel, tube, canister, spring, tears, pellets, frost, gas, bubble, backdrop) are procedural in our scripts.

## Trickiest shots and how
1. **Tear path face → tube → chamber.** Drops are keyed per frame from a sampled path: lower-lid point on the head bone → cheek surface (ray-cast against the evaluated face mesh, offset 1 mm) → funnel → tube curve points (evaluated each frame because the tube is hooked to the head and gun). Audit checks drop-to-skin distance.
2. **Cutaway dissolve.** Backdrop is a large curved sphere-cyc around the gun with an animated alpha; workshop lights fade down, studio softboxes up. Camera stays on the spline; no cut.
3. **Freezing.** Per-drop shader mix water → frosted ice keyed with staggered offsets; frost crystals are instanced spikes that scale up along the glass; plus a small cold fog volume.
4. **Memory transition (beat 9).** Camera rides the pellet into a full-frame defocus (aperture keyed wide), passes through the workshop's back wall (opening hidden in blur) into the office 12 m away; grade shifts cooler/desaturated.
5. **Crying acting.** Face bones keyed (brows, lids, mouth corners, jaw quiver), breathing sobs on spine/clavicles, hands-to-face with IK and audited fingertip-to-face distance (no penetration).
6. **Final shot contact.** Ice pellets travel a keyed ballistic path to the mentor's chest, puff spawned at the measured shirt surface; his recoil and laugh.

## Risks
- Time: ~5.5 h left. Blocking priority: camera path + all sets + both humans posed per beat; polish: hands/face/effects.
- CPU only (4 cores): stills at 270×480, 8 samples; volumes kept small.
