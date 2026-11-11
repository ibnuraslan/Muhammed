# Connect21: RingBullet

Branch `claude/connect21-ring-bullet`. Folder `blender/RingBullet_v001/`. Target length about 23.5 s, so frame_end = 1410. The script below is 75 words.

**Sensitive:** never show the robber's face or the gun pointed at camera. Show the injuries only as a small cut and a bandage, with no blood.

## Script (ours)

The robber fired the gun straight at his head, but at that exact moment, the man threw his hands up to cover his face. And instead of going through his skull, the bullet hit his wedding ring. It glanced off the metal and split into two pieces. One piece lodged in his finger, and the other went into his neck. But apart from some minor injuries and a dented ring, the man walked away okay.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The robber fired the gun straight at his head | A cosy study or shop at night, wood panels and warm lamps. A middle-aged bald man in shirt and tie, terrified. The robber is a dark silhouette or arm only, in the foreground. Muzzle flash, and the bullet launches in slow motion; the camera rides it. |
| 2 | 2.7 | threw his hands up to cover his face | Reverse slow motion: his hands snap up in front of his face with fingers spread and a gold wedding ring glinting. |
| 3 | 6.8 | instead of going through his skull | Macro: the bullet crawls toward his hand and head; rack focus. |
| 4 | 9.0 | the bullet hit his wedding ring | Impact on the ring: sparks and a metal flash; the hand jolts. |
| 5 | 11.0 | glanced off the metal and split into two pieces | Slow-motion macro: the bullet deforms and splits into two fragments flying apart. |
| 6 | 14.4 | One piece lodged in his finger | A fragment tracks to the finger, a small nick, and he winces. |
| 7 | 16.3 | the other went into his neck | The other fragment grazes his neck (shown as a quick flick and a small mark), and his hand flies to his neck. |
| 8 | 17.9 | minor injuries and a dented ring | He looks at the dented, bent ring on his finger in disbelief. The camera orbits close. |
| 9 | 20.8 | walked away okay | Wider: with a bandaged finger and a small neck plaster, he walks out past police lights (blue and red glow). Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/RingBullet_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
