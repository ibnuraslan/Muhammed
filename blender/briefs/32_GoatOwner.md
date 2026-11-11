# Connect32: GoatOwner

Branch `claude/connect32-goat-owner`. Folder `blender/GoatOwner_v001/`. Target length about 36.5 s, so frame_end = 2190. The script below is 95 words.

**Sensitive:** this film shows animal abuse and a death.
- Show the abuse only as a raised stick, the goat flinching and backing away, a shadow, and its tense posture. Never show the impact on the animal.
- The attack is a charge and an impact moment with the man doubling over. No blood or wounds.
- The death is implied: he lies still, seen from a distance.
- Use a real CC-BY goat model (or the goat rig from goat_rescue2) and a rural farm setting.

## Script (ours)

The owner would beat his goat with sticks, trying to make it aggressive toward people so it would guard his property. And this went on for a long time. But one day, the goat had enough. It charged forward and rammed its sharp horns straight into the man. Twice. As he stumbled away, the goat chased him onto the porch and knocked him off. He hit the ground hard and died within minutes. When his body was found, the goat was captured. But instead of being put down, it was taken in by animal rescuers.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The owner would beat his goat with sticks | A rundown rural farmyard: a rough man raises a stick over a tethered goat, which flinches and pulls on its rope (no contact shown). Dust, a broken fence. |
| 2 | 3.1 | to make it aggressive… guard his property | The goat stands rigid, eyes wide, ears back, snorting at a passer-by at the fence. |
| 3 | 7.7 | this went on for a long time | A time-lapse: seasons change and the goat grows thinner and scarred (subtle), tethered by the shed. |
| 4 | 10.5 | one day, the goat had enough | Close on the goat's eye and lowered horns, its hoof stamping. The man approaches with the stick. |
| 5 | 13.6 | charged forward and rammed its horns | Slow motion: the goat charges and slams into the man's midsection. He doubles over with dust exploding (no blood). |
| 6 | 18.8 | Twice. | A second impact in a quick slow-motion repeat. |
| 7 | 19.7 | stumbled away… chased him onto the porch | He staggers up the wooden porch steps clutching his stomach, the goat right behind him. |
| 8 | 23.6 | knocked him off | The goat butts him off the porch edge and he falls. |
| 9 | 25.3 | hit the ground hard and died within minutes | He hits the dirt and lies still. The camera slowly pulls away and up; the wind blows and dust settles. |
| 10 | 28.9 | the goat was captured | Officials with a catch pole and rope lead the goat into a trailer, while police tape flutters. |
| 11 | 31.8 | taken in by animal rescuers | An animal sanctuary in green pasture: rescuers stroke the goat, which calmly eats from a hand. Settle. |

## Rules for this film (on top of `pipeline/CONNECT_BRIEF.md` and `PRODUCTION_RULES.md`)
- **Script:** use the script below; it's ours. The reference narration is not in this repo; don't try to get it.
- **Timing:** with no voiceover yet, build to the **target times** in the beat table (they match the reference's pacing, about 2.8–3.2 words/s).
  - Write `beats.json`: `[{"beat": 1, "frame": <start frame>, "first_words": "..."}, ...]`. When the VO arrives, the director retimes with `pipeline/retime_to_vo.py`.
- **One continuous camera.** The reference cuts all the time; we don't.
  - Turn each cut into a move: dive through skin into a cross-section, fly through a wall, whip-pan, rack focus, or orbit from the character to a macro.
- **No on-screen text or captions** (captions are added in the edit).
  - No logos, brand names or watermarks on anything: clothes, cups, monitors, props.
  - No likeness of any real person; use generic characters.
- **Look:** textured, grounded realism, with anatomy believable and clean, never gory.
  - Medical "inside the body" beats use the clean explainer look: a deep teal-to-navy studio gradient behind realistic anatomy and studio lighting.
  - Real-world beats use real sets.
- **Deliverable tonight:** checkpoint D package in `blender/GoatOwner_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
