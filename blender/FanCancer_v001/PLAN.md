# FanCancer_v001: plan (Checkpoint A)

Connect30 · branch `claude/connect30-fan-cancer` · 1080×1920, 60 fps, frame_end 2640 (44.0 s) · Cycles CPU, AgX Medium High Contrast.

## Conflicts between briefs, and what I chose
- `30_FanCancer.md` says "pushed with Git LFS, under 150 MB". The Batch 2 rules and `CONNECT_BRIEF.md` say **no LFS, under 95 MB, normal git file**. I follow the newer rule: under 95 MB, no LFS.
- The film brief says medical cutaways use a "soft cyan-to-white gradient". Batch 2 rule 3 says cutaways use a **deep teal-to-navy gradient**, never pale. I use deep teal to navy, with a cyan rim light so the tissue still reads clean.

## World layout (one scene, one camera, all sets in one world)
The sets sit far apart in one scene. The camera travels between them only through motivated passes (skin, phone screen, tunnel wall, laptop screen), each one 6 frames or fewer and covered in macro texture.
- **RINK** at the origin: an ice sheet with boards and glass, the bench, a 6-row stand of seated MPFB crowd (instanced, with animated sway, cheer and phones), skaters looping on the ice, an arena light rig, haze.
- **SKIN** cutaway at x=+200: a displaced skin slab with a mole (irregular border, colour variation), an epidermis/dermis cross-section with SSS layers and abnormal cell clusters (instanced, displaced, wet SSS), vessels, and a teal-navy gradient.
- **TUNNEL to CLINIC** at y=−40: a concrete rink tunnel opens onto a clinic exam room (exam bed, cabinet, monitor with a pulse trace, lamp, a nurse moving in the background).
- **CITY** at x=−300: a night city block of buildings (Objaverse) with windows; small glowing phone and screen cards in windows and on a moving bus, with share or heart icons only.
- **HOME** at x=−300, inside one window: her living room (sofa, lamp, laptop on a video call, TV flicker, cat or plant motion).
- The **finale** happens back at the RINK set, relit and dressed with confetti and both teams.

## Characters (MPFB2, CC0 MakeHuman assets)
- **Her (the fan):** young woman, beanie and scarf (MPFB proxy hat and scarf, or a fitted cloth mesh on the head bone with Child Of), winter coat, and a phone in her hand (the phone parented to the hand bone, with the fingers posed around it).
- **Him (the equipment manager):** man in his 40s, plain dark team jacket with no logo, cap optional (if worn, on the head bone). The mole is a decal and displacement on the left back of his neck.
- **Dermatologist and nurse:** scrubs or white coat, hands on the dermatoscope or forceps.
- **Crowd:** about 8 MPFB variants instanced about 120 times with per-instance time offsets on 4 looping actions (sway, cheer, clap, phone up).
- **Players:** 6 to 10 MPFB bodies in plain jerseys of two colours (no numbers or logos), with helmets on the head bone and sticks in the hands.
Faces: brows, lids, jaw and lips keyed through the MPFB face bones on every emotional beat (focus, worry, puzzled, relief, shock, joy).

## Beat table (frame = t × 60; the camera is one spline, with a new framing about every 1 s)
| # | t | Frame | Line | On screen | Camera (continuous) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | "At a hockey game, she spotted a strange mole" | A packed rink, skaters crossing, puck chatter, the crowd swaying and cheering. She sits in row 1 behind the glass, then leans forward, eyes narrowing. | Open high over the ice (crowd and skaters), descend fast toward the glass at 0.0–1.2 s, then push through the crowd to her face 1.2–2.2 s, low 3/4 view. |
| 2 | 2.2 | 132 | "on the back of a man's neck" | Over her shoulder, through the glass: he stands at the bench below in a dark jacket, and the mole is visible on his neck. | Swing over her shoulder 2.2–3.0 s; focus pull from the glass smudge to his neck (rack focus) 3.0–3.9 s. |
| 3 | 3.9 | 234 | "It was an odd color, and she thought it could be cancer" | Macro on the mole (irregular, two-tone brown to black), then a dive through the skin into the cross-section: epidermis, dermis, abnormal dark cells branching down, and vessels. | Push to macro 3.9–5.0 s; pass through the skin (5 frames, pore detail) 5.0–5.1 s; drift down the cross-section 5.1–6.5 s; lateral orbit along the spreading cells 6.5–8.2 s. |
| 4 | 8.2 | 492 | "She was nervous about upsetting a stranger, but someone had to warn him" | Back on her: biting her lip, eyes darting to the fans beside her (who cheer and pay no attention), hand half-raised then pulled back, and finally a decisive nod. | Pull back out of the skin (reverse pass), whip back up to her 8.2–9.0 s; slow arc around her face 9–10, 10–11, 11–12 s (each a new side or height); push in on the nod 12–13 s. |
| 5 | 13.0 | 780 | "So she typed a note in big letters on her phone" | Her thumbs typing; the screen shows huge blurred, unreadable glyph blobs that grow line by line. | Dive over her shoulder to the phone 13.0–14.0 s, then top-down on the thumbs 14–15 s, then tilt up across the screen 15–15.8 s. |
| 6 | 15.8 | 948 | "and pressed it against the glass" | She slaps the phone flat on the glass and knocks twice with her other knuckles; the glass shudders. | Pull back fast with the slap 15.8–16.6 s; swing around the edge of the glass to his side 16.6–17.8 s (the phone is now seen from behind the glass, letters mirrored and blurred). |
| 7 | 17.8 | 1068 | "The team's equipment manager read the message, but walked away without saying a word" | He turns, squints and leans in (puzzled brows), looks up at her, then shrugs and walks off down the tunnel; players skate past behind him. | Over his shoulder on the phone 17.8–19.0 s; on his puzzled face 19–20 s; track behind him as he walks 20–21.2 s; follow into the tunnel 21.2–22.2 s. |
| 8 | 22.2 | 1332 | "Still, he went to a doctor just in case" | The tunnel's end-door opens into the clinic; he sits on the exam bed; the dermatologist leans in with a dermatoscope at his neck; a nurse at the cabinet; the monitor trace runs. | Fly through the tunnel door into the clinic 22.2–23.0 s; orbit the bed 23–24 s; push to the dermatoscope lens on the mole 24–25 s. |
| 9 | 25.0 | 1500 | "and when they checked the mole, they found cancer, which they quickly removed" | The doctor's face turns serious and she nods; a clean excision (gloved hands with forceps and a small dressing, no blood detail); then a bandage goes on, he exhales, and the doctor smiles. | Close on the doctor's face 25–26 s; overhead on the hands 26–28 s; side view as the bandage is placed 28–29 s; on his relieved face, pulling back 29–30.8 s. |
| 10 | 30.8 | 1848 | "He asked people to help him find the woman" | He holds his phone and posts (a large share icon pulses, no text); notification rings fly out. | Push into his phone screen 30.8–31.8 s; pass through the screen glow (4 frames, pixel-grid detail) into the night CITY; pull back up as windows light up with phones 31.8–33.8 s. |
| 11 | 33.8 | 2028 | "Strangers shared the story" | A bus passes with riders holding glowing phones; windows full of screens; share and heart icons jump between them. | Fly alongside the bus 33.8–34.8 s, then rise to a window 34.8–35.6 s. |
| 12 | 35.6 | 2136 | "and when she was finally identified" | Through the window into her living room: she is on a laptop video call (the call frame shows a blurred face, no text) and claps her hand to her mouth, eyes wide. | Glide through the window 35.6–36.4 s; arc to her shocked face 36.4–37.9 s. |
| 13 | 37.9 | 2274 | "both teams surprised her with a ten thousand dollar scholarship…" | At the rink centre: players of both teams in plain jerseys, him beside her, and her holding a big blank cheque. Confetti falls, the crowd stands and cheers, flashes pop, and players tap their sticks. | Push into the laptop screen, which shows the rink (screen pass, 4 frames), and come out at ice level in the RINK 37.9–39 s; orbit low around the group 39–41 s; crane up and over 41–43 s; settle wide high 43–44 s. |

`beats.json` will hold exactly these start frames.

## Assets and licences
- **MPFB2 / MakeHuman** system assets (CC0): every human, the clothes, hair, eyebrows and skins.
- **Poly Haven (CC0):** an indoor arena or warehouse HDRI (for example `industrial_sunset_puresky` as fallback, or `indoor_pool`); textures `concrete_floor_02`, `painted_plaster_wall`, `wood_floor`, `fabric_pattern`, `leather_red` (sofa); a model for the sofa, lamp and plants if present.
- **Objaverse / Sketchfab (CC-BY / CC0)** via `find_models.py`: hockey rink or arena seats, hockey players or skates and sticks, a smartphone, a dermatoscope or otoscope, an examination table, a city block, a bus, a laptop. Each one is checked on the thumbnail sheet; every CC-BY model goes in `CREDITS.md`.
- **Procedural only where nothing exists:** the ice (scratched, displaced, with a glossy coat), the skin cross-section (layered displaced mesh with SSS, noise-driven pores, and instanced displaced cells), confetti (particles), and the blurred phone glyphs (an emission texture from heavily blurred noise blobs, no letters).

## Trickiest shots and how I'll do them
1. **Skin dive (beat 3).** A hi-res displaced skin patch made from a pore and wrinkle noise stack, with a mole made from a Voronoi plus noise mask and a 3-tone colour ramp. The camera crosses it in 5 frames while the surface fills the lens with pores. The cross-section uses 3 layered displaced sheets (epidermis, dermis, fat) with SSS, plus geometry-node instanced irregular cells (displaced icospheres, not smooth: noise displacement and Voronoi albedo).
2. **Glass swing (beat 6).** The glass is a real transmissive pane with smudge roughness. The camera arcs around the pane edge, so it never passes through the pane.
3. **Phone in hand, flat on the glass.** The phone is parented with Child Of to the right hand bone; the fingers are posed per key; the glass contact is checked numerically (a phone-to-glass gap under 3 mm, no overlap).
4. **Crowd density at low cost.** Instanced MPFB variants (collection instances with offset actions) and decimated distant rows.
5. **Screen passes (beats 10 and 13).** A pass through a phone or laptop: an emission screen with a sub-pixel grid texture fills the frame for 4 frames or fewer, and the next set is already lit behind it.
6. **Package size.** 1K textures (2K on skin and her face), a 1K HDRI, a decimated crowd and city, `compress=True` and an orphan purge. Target 60–90 MB.

## Schedule (UTC, compressed)
A ≈ 22:15 · B by 23:45 · C by 01:15 · D by 02:15 (`blender/FanCancer_v002/`, under 95 MB, no LFS).
