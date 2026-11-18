# Competitor 05 · Fern — "The Kid Who Ruled 33% of the World" (Puyi, last emperor of China)

| | |
|---|---|
| Source | Drive `competitors/…fern (1080p).mp4`, 21:57, **1920×818 = 2.35:1** (21:9), 25 fps |
| Shots | 149 · **median 6.4 s** (slow, contemplative) · p10 2.2 s · p90 19.5 s |
| Sound | −14.2 LUFS integrated, LRA 4.8 LU (widest dynamics of all refs) |
| Contact sheet | `05_fern-puyi.jpg` (all 149 shots) |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.04 · median 0.23 · p95 0.75 |
| Saturation | Median 0.34, **p90 0.80** → very strong accent colours |
| Palette | `#0c090c` black 17% · `#241317` 11% · `#252a32` slate 11% · `#3c4650` 10% · `#b99a7c` parchment 9% · `#81685f` 8% · `#d7c6c2` 8% · **`#581717` / `#932421` imperial red 12%** · `#b4683f` gold 4% · `#456c81` teal-blue 4% |
| Colour script | **Each era has its own palette**: imperial court = saturated red + gold on black · palace exteriors = pink-violet haze · Japanese occupation = teal/blue · prison = blue-grey · old age = bright daylight |
| Render | Stylised-realistic 3D, closer to a feature animation than to Yarnhub's game look: soft skin, large expressive eyes on the child, saturated sets |
| Devices | Parchment date cards ("November 13, 1908 / Beijing, China") · vintage maps with red route lines · paper timeline · archival portrait cards on parchment · **3D characters standing on blown-up archival photos** (Johnston on a 1919 street photo) · numbers appearing inside the 3D set ("1 8 5 2") · hands holding real photos with a red circle |

## Characters and staging

| Item | Obs | Lesson for Seldom |
|---|---|---|
| Child protagonist | Large-eyed child model; expressions read clearly at MCU/ECU; mostly **seated on the throne** | Seated hero = no walk problem, maximum face time |
| Adults | Full-body standing figures in **pools of light on black** (Johnston in a spotlight) | Standing still in a spotlight avoids locomotion |
| Processions | Crowds of officials and horses in long wides in haze | Crowds only as silhouettes in atmosphere |
| Hands | Hands holding photos (inserts), the child's hand on fabric | Inserts only |
| ECU faces | Empress Dowager's face in a 35 s hold, eyes and lips | Long face holds with subtle animation |
| Shot length | Many 10–37 s holds; lots of slow pushes | Fern trusts the frame; pacing comes from the VO |

## What Seldom can take

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | **Colour script per era/chapter** (measured: red/gold court, teal occupation, blue-grey prison) | `look.py` chapter presets driven by the EDL | Easy |
| 2 | Seated or still protagonist in a spotlight on black | Staging rule + void preset | Easy |
| 3 | 3D character composited onto a blown-up archival photo | Photo plane as the set, character on top with a contact shadow | Easy |
| 4 | Parchment date/portrait cards, vintage maps with red routes | `title_card.py` parchment variant | Easy |
| 5 | Long face holds (20–35 s) with micro-animation (blinks, breathing, eye darts) | Face rig + idle layer (see GAP_ANALYSIS 1.4) | Medium |
| 6 | 2.35:1 at 1920×818 | Same as ours (1920×816) ✔ | Done |
