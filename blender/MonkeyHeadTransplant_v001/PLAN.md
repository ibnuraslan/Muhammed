# MonkeyHeadTransplant: plan (checkpoint A)

- **Film:** 29.5 s, frames 1–1770 at 60 fps, 1080×1920, Cycles on CPU.
- **Camera:** one camera, `CAM_Film`, on one Catmull-Rom spline. Camera, aim and lens are sampled every 3 frames, and there are no cuts or camera markers.
- **Script:** the 80-word script from the brief, timed to the target beat times (`beats.json`).

## Sets (one continuous world, about 9 × 7 m)
- **OR, 1970s.** Pale green tiled walls (Poly Haven tiles), with a worn terrazzo or lino floor.
  - Two chrome operating tables side by side, with green vinyl pads and white drapes.
  - A big dome surgical lamp on a ceiling arm, which glints and swings slightly.
  - An instrument tray on a teal trolley (`cart.glb` + `tools.glb`).
  - A frosted glass partition behind, with a soft cyan gradient glowing through it ("cyan studio gradient beyond").
  - Also: an IV stand, a wall clock with no numbers or text, and a bowl.
- **Recovery corner** in the same room, about 3 m to the right: a wooden armchair (`chair.glb`), a 1970s round-screen oscilloscope used as the heart monitor (`scope.glb`) with our own animated green ECG trace on its screen, and a side lamp.
- **X-ray studio:** the recovery corner with its walls, chair and props faded to a cyan-to-white studio gradient. That is the "dive through the skin" space.

## Characters
- **Monkey A (head donor):** `monkey.glb`, "Realistic Monkey" by TdoubleU8 (CC-BY), a rhesus-like macaque with a pink face and pale fur.
  - It's split at the neck into `MonkeyA_Head` and `MonkeyA_Body`.
  - Sedated, it lies curled on its side on table 1.
- **Monkey B (body):** the same mesh with a ginger hue shift, lying on table 2. Its head is hidden; a smooth draped stump is covered by a cloth.
- **Composite:** head A on body B. It is rigged with my own armature (spine, neck, head, 4 limbs, tail) using automatic weights.
- **Extra detail I'll add** for the acting the brief needs:
  - Eyeball spheres with a procedural brown iris that track a target.
  - Skin-coloured eyelid shells that blink.
  - Ear bones that twitch.
  - A neck seam ring with stitches revealed one by one.
- **Surgeon:** an MPFB2 human in a gown tinted surgical green, with a procedural cap, mask and pale gloves.
  - IK hands do a real grasp: marker on the neck, then both hands under the head, lift, place, then the needle holder.
  - The surgeon's weight shifts, the torso turns, and the head bobs.
- **Assistant (background, busy):** an MPFB2 human who adjusts the lamp, hands over tools, and then checks the monitor.
- Generic people, no likeness, no text or logos anywhere.

## Beat table (target start times; one framing about every 1 s, all one move)
| # | t (s) / frame | Line | On screen | Camera (framings) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | In 1970, a surgeon removed the head | Wide OR: lamp swings on, the surgeon leans over monkey A and draws the neck line with a marker (a dashed line appears), and the assistant wheels the tray in. The cyan glow comes through the glass. | 0.0 low dolly between table legs → 1.0 rise past the tray → 2.0 over the surgeon's shoulder → 3.0 close on the neck line being drawn → 4.0 pull up as the hands slide under the head |
| 2 | 4.3 / 259 | attached it to the body of another one | The hands lift head A (clean, draped; the neck underside is a smooth covered stump, no gore), the torso turns, and the head is set onto the ginger body on table 2. | 4.3 crane up and over the top → 5.3 top-down as the head travels between the tables → 6.0 descend toward table 2 |
| 3 | 6.5 / 391 | carefully joining the tissue in the neck | Macro on the seam: the needle holder arcs the curved needle through, thread pulls taut, and stitches appear one by one. Forceps come in, and lamp glints sweep across the steel. | 6.5 drop to macro → 7.5 orbit 1 → 8.5 orbit 2 (low, the lamp flares behind) → 9.5 under the hands → 10.5 rise to the face |
| 4 | 11.2 / 673 | incredibly, the monkey survived | Slow push to the face: the eyelids flicker, open, then blink twice. A finger twitches. | 11.2 three-quarter close → 12.2 push → 13.2 extreme close on the eyes → 14.2 ease off |
| 5 | 14.8 / 889 | could still see and hear | The eyes track the camera as it orbits. The assistant drops a steel bowl (a clang), and the ear twitches toward it while the eyes dart. | 14.8 orbit start → 15.8 orbit over the brow → 16.6 dive into the neck seam (skin fills the frame) |
| 6 | 17.1 / 1027 | spinal cord couldn't be reconnected | We come out in the cyan studio: the monkey sits in the chair, its body translucent green x-ray, with a glowing brain and spinal cord. At the neck there's a visible gap where the cord ends in two glowing stubs; a red pulse runs down from the brain and stops at the gap. | 17.1 emerge close on the neck gap → 18.1 orbit down the spine → 19.1 rise back to the brain |
| 7 | 20.1 / 1207 | couldn't move its body at all | The x-ray fades back to fur and the room returns around it. Wide: the monkey slumps in the chair, arms limp, its head lolls a little, and only the eyes move side to side. The assistant waves a hand and the body does not react. | 20.1 pull back → 21.1 low wide → 22.1 lateral drift |
| 8 | 23.2 / 1393 | technically a success | The camera drifts to the 1970s oscilloscope heart monitor: a green trace beeps (pulse flash) and the surgeon's hand notes on a clipboard. | 23.2 track to the monitor → 24.2 close on the trace → 25.2 sweep past the screen |
| 9 | 26.0 / 1561 | only lived for a few more days | The trace slows, gets flatter, and goes flat. The lamp dims, the window light shifts, and dust drifts. A slow pull-out to the wide room, with the monkey small in the chair. | 26.0 pull from the screen → 27.0 rise → 28.5 wide end |

## Assets and licences (downloaded; in `assets/credits.json`)
| Asset | Source | Licence |
|---|---|---|
| Realistic Monkey: TdoubleU8 | Sketchfab 50e4b1da (via Objaverse) | CC-BY |
| Human Brain: 3DRT STUDIOS | Sketchfab 7a27c17f | CC-BY |
| SURGICAL INSTRUMENT: ferofluid | Sketchfab 2971a44d | CC-BY |
| Oscillscope310a: hughzey3 | Sketchfab 7c653d3f | CC-BY (any labels will be removed or retextured) |
| Karol Szymanowski's Armchair #1: Virtual Museums of Małopolska | Sketchfab 07518472 | CC-BY |
| Medical Cart: NicolasVB | Sketchfab 2a0a574f | CC-BY |
| Tiles, terrazzo, metal and fabric textures, and the HDRI | Poly Haven | CC0 |
| MPFB2 humans and clothes | MakeHuman system assets | CC0 |
| Procedural (mine) | tables, lamp, eyes, eyelids, stitches, spine, x-ray, ECG trace, partition, IV stand | n/a |

## Trickiest shots and how I'll do them
1. **Head transfer, beat 2.**
   - Both monkeys are the same mesh, so A's head fits B's neck exactly.
   - The head object is driven by a CHILD_OF constraint on the surgeon's hand: influence 0 → 1 at the grasp and 1 → 0 at the placement. The hands are keyed with IK to the head's surface.
   - The neck faces are capped with a smooth, skin-pink, draped surface (no blood). A white gauze ring hides the cut on both sides.
2. **Eyes and blinks.** The model's eyes are painted in its texture. I'll add real eyeballs and eyelid shells, fitted numerically to the eye sockets and checked in close-up stills.
3. **X-ray, beat 6.** A copy of the composite gets a fresnel green glass material. The brain is `brain.glb`, scaled to the macaque skull and emissive pink.
   - The spinal cord is a procedural tube with vertebra rings.
   - The gap is a 3 cm break with glowing ends.
   - The transition is a dive into the neck seam: macro → skin fills the frame → the cyan world. The camera spline passes through the seam, so it reads as flying through the skin, not as a cut.
4. **Limp body, beat 7.** I'll pose the rig as a slump (spine side-bend, head tilt, arms dangling over the armrests). The motion is only eyes and tiny breathing, plus an assistant waving a hand for contrast.
5. **Contacts.** An audit script will check monkey on table, monkey in chair, surgeon's feet on the floor, hands on the head, and the camera inside geometry.

## Schedule
- B blocking at 21:45.
- C polish at 23:45.
- D package at 01:00, as `blender/MonkeyHeadTransplant_v002/`.
