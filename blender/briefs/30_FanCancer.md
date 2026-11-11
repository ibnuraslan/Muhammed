# Connect30: FanCancer

Branch `claude/connect30-fan-cancer`. Folder `blender/FanCancer_v001/`. Target length about 44.0 s, so frame_end = 2640. The script below is 131 words.

Real people: use generic faces. No team logos, names or jersey numbers on anything. Her phone note shows as large blurred, unreadable letters, and the cheque is blank.

## Script (ours)

At a hockey game, she spotted a strange mole on the back of a man's neck. It was an odd color, and she thought it could be cancer. She was nervous about upsetting a stranger, but someone had to warn him. So she typed a note in big letters on her phone and pressed it against the glass. The team's equipment manager read the message, but walked away without saying a word. Still, he went to a doctor just in case, and when they checked the mole, they found cancer, which they quickly removed. He asked people to help him find the woman. Strangers shared the story, and when she was finally identified, both teams surprised her with a ten thousand dollar scholarship as a thank you for saving his life.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | At a hockey game, she spotted a strange mole | An indoor ice rink: a packed crowd, players skating, the glass and the bench. A young woman in a beanie and scarf behind the glass leans forward, staring. |
| 2 | 2.2 | on the back of a man's neck | Her POV through the glass: a staff member in a team jacket, the back of his neck with a dark irregular mole. Rack focus. |
| 3 | 3.9 | an odd color… could be cancer | Macro dive into the skin: a realistic irregular mole, with a cross-section showing abnormal cells spreading. |
| 4 | 8.2 | nervous about upsetting a stranger | Back on her: biting her lip, glancing around, hesitating. |
| 5 | 13.0 | typed a note in big letters | Close on her thumbs typing; the phone screen shows big blurred letters (unreadable). |
| 6 | 15.8 | pressed it against the glass | She slaps the phone to the glass and knocks; the camera swings around the glass to his side. |
| 7 | 17.8 | read the message, but walked away | He turns, reads it with a puzzled face, then walks off down the tunnel. |
| 8 | 22.2 | went to a doctor just in case | A clinic exam room: a dermatologist with a dermatoscope examines his neck. |
| 9 | 25.0 | they found cancer, which they quickly removed | A small surgical excision (clean), a bandage, relief. |
| 10 | 30.8 | asked people to help him find the woman | He holds a phone and posts a message; the camera pulls back as phones light up across a city (icons only). |
| 11 | 33.8 | Strangers shared the story | A montage of many phones and screens glowing in homes and on buses, sharing. |
| 12 | 35.6 | when she was finally identified | She is at home on a video call, surprised, hand to her mouth. |
| 13 | 37.9 | both teams surprised her with a scholarship | At the rink: players from both teams (plain jerseys, no logos), the man, and her holding a big blank cheque, with confetti and a cheering crowd. Crane up and settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/FanCancer_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
