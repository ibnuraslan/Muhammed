# AIAsleep: plan (checkpoint A)

Connect29, branch `claude/connect29-ai-asleep`, folder `blender/AIAsleep_v001/`.
1080×1920, 60 fps, frames 1–2610 (43.5 s). One camera, one spline, no cuts. AgX Medium High Contrast.

## Beat table (frame = 1 + t×60)

| # | t (s) | frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | As he drove, the car's AI scanned his face | Night highway. Man (generic East Asian, 30s) drives a modern sedan; streetlights sweep through the cabin; a car overtakes. A small dash camera above the steering column sends a soft cyan scan beam (volumetric slit light) across his face; a faint face-landmark mesh (emissive dots/lines, shrinkwrapped on the skin) ghosts on and off. | Start outside the side window, low, tracking with the car (0–1 s) → push through the open window gap to a 3/4 front of him (1–2 s) → slide along the dash over the camera lens, beam in foreground (2–3 s) → his face lit by the sweep (3–3.9 s). |
| 2 | 3.9 | 235 | flashed red, warning him to wake up | Dash screen flips to a red closed-eye icon (icon only, no text); a red pulse ring expands on the screen; red interior lighting floods the cabin in 3 pulses; he flinches back. | Whip from his face down to the screen (3.9–4.6) → hold-drift on the icon with red pulse (4.6–5.6) → pull back to a wide cabin from the passenger seat, red everywhere (5.6–6.9). |
| 3 | 6.9 | 415 | confused, because he wasn't sleeping | Close on his face: brows knit, head tilt, eyes clearly open and normal, looks from road to screen and back; a lip purse. Traffic lights streak past behind him. | Push from wide to medium close on face (6.9–8) → slow arc left across the windscreen line (8–9) → tighter, eye-line with the screen (9–10.1). |
| 4 | 10.1 | 607 | sat up straighter to look more alert | He straightens his spine, rolls shoulders, gives a quick head shake, re-grips the wheel at 10 and 2 (IK hands planted on the rim). Screen still red-pulsing. | Orbit around the cabin behind the headrest (10.1–11) → over the passenger side (11–12) → front low through the dash, looking up at him (12–13). |
| 5 | 13.0 | 781 | nothing worked until he forced his eyes wide open | Two more failed tries (nod, blink hard) then he forces his eyes comically wide (lids up via face bones, brows high); the screen turns green with an open-eye icon, cabin light goes calm cyan. He holds the stare, strained. | Low dash angle (13–14) → push in on the eyes (14–15.5) → whip to the green screen (15.5–16.3) → rack back to his straining face over the screen (16.3–18). |
| 6 | 18.0 | 1081 | The moment they relaxed, the alarm went off again | Eyes relax back to normal → instant red flood again, icon flips red; he slumps, puffs a frustrated exhale (cheeks, shoulders drop), hand off the wheel in a small exasperated gesture, back on. | Side close (18–19) → drift to over-the-shoulder with red screen (19–20.4) → rise to the roof line, looking down through the cabin (20.4–21.7). |
| 7 | 21.7 | 1303 | twenty times on a single trip | Camera exits through the windscreen/roof: the car drives on the highway, time-lapse (world animation speeds up 6×): streetlight streaks, traffic, city towers passing, then the bridge; the cabin flashes red rhythmically (about 8 visible pulses). | Up through the sunroof glass (21.7–22.4) → chase from high behind (22.4–23.4) → swing round to the front 3/4 as the city slides by (23.4–24.4), drop back toward the windscreen and the dash camera. |
| 8 | 24.4 | 1465 | designed to beep whenever it couldn't see the iris | Fly into the dash camera lens → "the AI's view": the same face, now in a monochrome IR grade (world/material swap, one camera), with a 3D tracking box (emissive thin frame) locked around the eye, landmark dots, and an iris-detection circle that locks green when the iris shows and blinks red when it doesn't. | Through the lens glass (24.4–25) → straight-on to his face in IR (25–26) → push to the eye box (26–27.4) → small arc to the iris circle (27.4–28.8). |
| 9 | 28.8 | 1729 | naturally had epicanthic folds, where the skin of the upper eyelid overlaps near the nose | Out of the IR into true colour, macro on his eye: hi-res skin, lashes, the inner corner. The camera dives in: a clean cross-section plane opens through the upper lid and inner corner against a deep teal-to-navy studio gradient: skin, orbicularis muscle, the orbital fat, the fold of skin draping over the inner corner (medial canthus), the eyeball with the iris. Highlight tint (soft warm glow) on the fold as it is named. | Macro push on the inner corner (28.8–30) → dive through the skin (≤6 frames, macro detail) into the section (30–31) → slow orbit of the section, 3 framings (31–34) → track along the fold line toward the nose (34–36.9). |
| 10 | 36.9 | 2215 | forming a smooth flap that covers part of the iris | Back out to the surface macro: the fold visibly covers the inner part of the iris; the IR overlay circle flickers between red and green and fails. | Pull out of the section to the surface macro (36.9–38) → frontal eye with the failing circle (38–39.5) → lateral slide (39.5–40.8). |
| 11 | 40.8 | 2449 | making the AI think he was asleep | Pull back through the cabin: he sighs, shakes his head; the red icon blinks; the car drives away down the highway into the night. Settle. | Pull back out of the eye past his face (40.8–41.8) → back through the windscreen to outside (41.8–42.8) → settle on the car driving away (42.8–43.5). |

`beats.json` will carry these frames and first words for `retime_to_vo.py`.

## Assets (licences)
| Asset | Source | Licence |
|---|---|---|
| Sedan with interior ("SAAB 9-5 blue sedan" by blendffnike; badges removed, fallback "Volkswagen I.D.R with interior" by tulex_art for cockpit parts) | Sketchfab via Objaverse | CC-BY 4.0 |
| Steering wheel ("Steering wheel" by pampi2703) if the car's wheel is too low-poly | Sketchfab via Objaverse | CC-BY 4.0 |
| Realistic human eye (Alexander Antipov) for the cross-section eyeball | Sketchfab via Objaverse | CC-BY 4.0 |
| City ("City" by SpatialNeglect), road ("Road / Highway" by ROY), street light (aashifkamran23) | Sketchfab via Objaverse | CC-BY 4.0 |
| Driver: MPFB2 / MakeHuman human, middleage_asian_male skin, short hair, casual suit (print patched out), face bones for brows/lids/jaw | MakeHuman system assets | CC0 |
| Night HDRI (urban night), asphalt, leather, fabric, plastic textures | Poly Haven | CC0 |
| Dash screen icons (closed/open eye, pulse ring): drawn as emissive curves in Blender | ours | — |

## Trickiest shots and approach
1. **Epicanthic fold, respectful and accurate.** MPFB with asian phenotype already models the fold; I add a corrective shape key on the upper lid/medial canthus (sculpted from anatomical reference: the fold runs from the upper lid down over the inner corner, partly hiding the caruncle and the nasal edge of the iris when relaxed). No caricature: normal eye aperture, adult proportions. Hi-res via subdiv 2 for macros only.
2. **Cross-section (beat 9).** Boolean cut of a duplicated, subdivided MPFB eye region + the CC-BY eyeball; layered materials (epidermis/dermis SSS, red fibrous orbicularis, yellow lobulated fat with noise displacement, tarsal plate), wet specular, against a deep teal-to-navy gradient with studio key/rim. Through-skin dive limited to ≤6 frames with pore detail.
3. **AI view without a second camera.** The camera flies into the lens; a driver keyed on frame swaps the world and character materials to an IR monochrome grade and shows 3D overlay geometry (tracking box, landmarks, iris circle). Same camera throughout.
4. **Highway at night with one camera.** The car stays near origin; road, lights, traffic and city move past it (scrolling); speed ramps 6× in beat 7. Motion blur on for the streaks.
5. **Hands on the wheel.** MPFB IK control rig from `anim_lib.make_human_ctrl`; hand targets parented to the rim; numeric BVH check in the audit.
6. **Faces.** MPFB face bones (brows, lids, jaw, lips) keyed per beat: puzzled, strain-wide, relaxed, frustrated exhale, sigh.

## Notes / questions for the director
- The film brief asks for a cyan-to-white cutaway backdrop and LFS; the Batch 2 rules say deep teal-to-navy and **no LFS, under 95 MB**. I'm following Batch 2 (teal-to-navy, normal git file under 95 MB).
- Car badges and any dash text will be removed; screen shows icons only.
