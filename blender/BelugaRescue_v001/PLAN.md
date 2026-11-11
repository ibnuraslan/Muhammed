# BelugaRescue_v001 — PLAN (checkpoint A)

1080×1920, 60 fps, frames 1–2190 (36.5 s). One camera `CAM_Film` on one Catmull-Rom spline, one framing ≈ every 1 s, no cuts.
No VO yet: beats are built on the brief's target times; `beats.json` holds start frames for `retime_to_vo.py`.

## World (metres)
- **Tank**: 12 × 10 m, floor z = 0 (long white tiles, tinted pale aqua), water surface z = 6.0 (Ocean modifier, procedural, no cache).
  - Walls: sculpted "ice-rock" (rock_face_03 + snow_02 blend, displaced, cold white-blue) on three sides.
  - Front wall (−Y): big acrylic viewing window, 7 × 4 m, with a dim viewing gallery behind it: 5–6 MPFB spectators + a keeper in a navy polo (no logos).
  - Rim: concrete deck at z = 6.25 with a rounded coping edge and a steel ladder; 3 spectators + keeper on deck for the ending.
- **Water look**: volume scatter/absorption (cyan-teal, dims with depth), surface caustics via a gobo-textured spot (animated voronoi), 4 sun-shaft spots through the volume, floating ice chunks on the surface, procedural bubble field (Geometry Nodes, keyable "burst" inputs), fine particulate.
- **Explainer look (beat 3)**: when the camera reaches the calf macro, a soft cyan-to-white studio gradient card fades in behind the leg (parented to the camera) and a studio key/rim pair lights the X-ray. Then it fades back to the tank.

## Characters
- **Freediver** (MPFB female, young, athletic): `female_sportsuit01` re-shaded as a grey neoprene wetsuit (full-length), hair `ponytail01` (bun-like, tinted dark), procedural freediving mask (low-volume, Child Of head bone, offset shell, strap), long freediving fins (procedural blades, Child Of foot bones), no tank. MPFB default rig + `anim_lib` controls; mostly FK posing underwater, IK for hands on the edge.
- **Beluga** (own procedural model, ~4.3 m): lofted body with melon, short beak, neck crease, pectoral flippers, flukes; SSS white skin with subtle scars/noise; eye, mouth line and jaw-open shape key. Own 8-bone spine chain + neck/head + jaw, weights computed along the body axis. Swim = travelling sine wave on the spine (vertical fluke beats), banking, head turn.
- **Spectators / keeper**: MPFB humans (proxy-weight, subdiv 0), casual suits tinted, idle + react (pointing, hands on glass, cheering).

## Beat table (start times from the brief; camera framing ≈ 1 per s)
| # | t (s) | frame | Line | On screen | Camera |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | She dove into an Arctic whale tank | Deck-level wide: ice-rock tank, spectators behind glass below; she arches off the coping and pierces the surface; bubble trail, light rays | 0–1 s high over her shoulder on the deck → 1–2 s she leaves frame head-first, camera tilts down and **dives through the surface with her** (splash bubble wipe) → 2–2.8 s chasing behind/above her fins in the shafts |
| 2 | 2.8 | 169 | as she sank to the bottom | Duck-dive glide, slow fin kicks, she descends 6 m to the tiles; light dims (keyed volume density/exposure) | 2.8–3.6 s camera swings under her, looking up at her silhouette against the shafts → 3.6–4.4 s drops past her to floor level as she settles knees-down on the tiles |
| 3 | 4.4 | 265 | the freezing water sent her legs into crippling cramps | Her calves seize: toes point, knees jerk, hands grab the calf; frost-blue chill rim; X-ray porthole on the calf: gastrocnemius knots with a red pulse on a cyan-white studio gradient | 4.4–5.4 s low skim along the tiles to her legs → 5.4–6.4 s push in to the calf macro (lens 30→70), gradient card fades in → 6.4–7.6 s slow orbit around the X-ray calf, red pulses on "crippling cramps" → 7.6–8.7 s pull back out, gradient fades, tank returns |
| 4 | 8.7 | 523 | impossible to swim back up | She claws upward (big breast-stroke arm pulls), legs locked straight, rises ~0.8 m and sinks back to the floor; panic bubble bursts | 8.7–9.7 s crane up past her to look down at her reaching toward the surface → 9.7–11 s the camera drifts down with her as she sinks back |
| 5 | 11.0 | 661 | as she started to drown | Face close-up in mask: cheeks puffed, eyes wide, last bubbles escaping from the lips | 11–12 s push in from the side to her mask (lens 50) → 12–12.9 s arc around the face to her other side, bubbles stream up past the lens |
| 6 | 12.9 | 775 | a beluga whale noticed her panicking | The white beluga glides into view behind her, cruising past ice-rocks; its head turns toward her | 12.9–13.9 s rack focus from her face to the whale behind (DOF focus object moves) → 13.9–15.4 s orbit around the whale's head as it turns |
| 7 | 15.4 | 925 | known for being intelligent and playful | Vignette in the same tank (whale glides toward the window): it bats a floating orange ring, spins, nods at the keeper behind the glass, who nods and gestures back; spectators press the glass | 15.4–16.4 s fly along beside the whale to the window → 16.4–18.4 s orbit the ring play → 18.4–20.2 s whip-pan from the keeper's face back to the whale |
| 8 | 20.2 | 1213 | it could tell something was wrong | Macro on the beluga's eye; it blinks, the head snaps toward the diver; tail pumps and it surges | 20.2–21.2 s macro push on the eye → 21.2–22.9 s pull back and ride along its flank as it surges to her (speed ramp) |
| 9 | 22.9 | 1375 | gently took her leg in its mouth | Whale dips under her, opens its mouth, gently closes on her ankle (lips only, no teeth); then turns nose-up and pushes her upward with powerful fluke beats | 22.9–24 s close on the ankle/mouth contact → 24–26 s pull back low as both start rising, camera beneath them looking up → 26–28.3 s spiral crane up around them |
| 10 | 28.3 | 1699 | just as she was about to run out of breath | Her eyes flutter, last bubbles stop; vision blur (DOF wide open + vignette, slight grey grade); they race up through the light shafts | 28.3–29.3 s on her face, lens 45, shallow focus → 29.3–31.4 s camera races up alongside them toward the bright surface |
| 11 | 31.4 | 1885 | lifted her above the surface | They break the surface in a splash crown; camera breaches with them (half-under/half-over pass), water sheets off | 31.4–32.4 s just below the surface looking up → 32.4–34.2 s camera bursts out above the water, circling the splash |
| 12 | 34.2 | 2053 | she could finally gasp for air | She gasps and coughs, mask pushed up, clinging to the coping; beluga circles beside her and spouts; spectators on deck cheer, keeper kneels with a hand out | 34.2–35.2 s close on her face at the edge → 35.2–36.5 s slow rise and pull back to reveal whale, deck and cheering people. Settle. |

## Assets and licences
| Asset | Source | Licence |
|---|---|---|
| Freediver, spectators, keeper | MPFB2 + MakeHuman system assets | CC0 |
| Beluga, mask, fins, ring, ladder, ice chunks, bubbles, tank | built procedurally in our scripts | own |
| HDRI `events_hall_interior` (above-water hall) | Poly Haven | CC0 |
| `long_white_tiles`, `rock_face_03`, `snow_02` | Poly Haven | CC0 |
No CC-BY models are needed so far (the Sketchfab belugas were too low-poly or game rips, so I build our own).

## Trickiest shots and how
1. **Camera through the water surface (beats 1 and 11).** Ocean surface is a thick-ish plane; the camera crosses it in ≤ 3 frames, masked by a splash/bubble burst. Above water the world is the HDRI hall; below, volume + fog.
2. **Calf X-ray in the explainer look (beat 3).** Porthole shader on body + wetsuit materials (as in goat_rescue2), procedural gastrocnemius/soleus meshes Child Of the lower-leg bone, red emission pulse, gradient card parented to the camera.
3. **Mouth on the ankle (beat 9).** The whale is driven from her ankle each frame: the mouth socket empty is solved to the ankle world position (no gap, no penetration — checked by BVH), jaw shape key closes to lip contact.
4. **Pushing her upward (beats 9–11).** Her root follows the whale's head path; legs/arms secondary motion via sine-lagged FK.
5. **Clinging to the edge (beat 12).** IK hands on the coping top (contact checked), forearms over the edge, body hanging in the water.
6. **Contact audit:** BVH overlap for hands, feet, fins, mask vs. scene and each other; mask–head gap; floor penetration at the bottom beats; camera-inside-geometry check.

## Schedule (UTC)
A 19:55 · B 23:15 (1/s sheet + camera path) · C 00:45 (0.2 s sheets + audit) · D 01:30 package in `blender/BelugaRescue_v002/`.
