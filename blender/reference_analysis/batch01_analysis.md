# Reference analysis — batch 01 (5 videos, Zack D. Films style)

Videos: shark finning (31 s), Elvis/constipation (31 s), spotlight effect (47.6 s), multiplane camera (40.3 s), rock-paper-scissors robot (30.9 s). All 720×1280 at 29.97 fps as received.
Method: every frame decoded; 2 fps contact sheets read shot by shot; frame-difference curve at full frame rate; narration transcribed with word timestamps (faster-whisper small.en).

## Hard numbers
| | Shark | Elvis | Spotlight | Multiplane | RPS robot |
|---|---|---|---|---|---|
| Length | 31.0 s | 31.1 s | 47.6 s | 40.3 s | 30.9 s |
| Words | 85 | 80 | 114 | 115 | 86 |
| Narration speed | 2.79 w/s | 2.61 w/s | 2.54 w/s | 2.91 w/s | 2.85 w/s |
| Narration starts | 0.00 s | 0.00 s | 0.00 s | 0.00 s | 0.00 s |
| Silence after last word | 0.6 s | 0.5 s | 2.6 s | 0.7 s | 0.7 s |
| Longest pause | 0.42 s | 0.42 s | 0.56 s | 0.56 s | 0.42 s |
| Near-static picture (whole video) | 1.0 s | 1.3 s | 0.7 s | 0.8 s | 2.6 s |
| Hard cuts | ~0 | 0 | ~1 (white flash) | 0 | 0 |

- **Something changes every 0.5 s.** The caption changes every ~0.5–0.8 s (1–3 words each). A new camera setup or composition arrives every ~1.5–2.5 s. The camera is never locked off: under ~1 s of near-static picture in a 30–48 s video.
- **No hard cuts.** Setups are joined by motion: whip-pans with heavy motion blur, flying *through* an object (door, shirt, wall, cable), push-ins into a detail, zoom-blur, cloud/particle wipes and the occasional white flash. The viewer never sees a "cut".
- **Wall-to-wall narration.** It starts on frame 1 and stops at the end. No title, no intro, no outro, no pause longer than ~0.5 s.

## Script structure (all five)
1. **Line 1 is the hook and is already mid-action.** "They use a sharp knife…", "He was found dead on his bathroom floor…", "A pretty girl waves at you.", "As you play scissors…". No "did you know", no context first.
2. **Mechanism in plain words,** one short clause per visual beat.
3. **A turn:** "But…", "So some people think…", "You see, if you…".
4. **Payoff line** that ends the video: a consequence ("millions of sharks die every year for no good reason"), a delayed reveal (the name *Elvis Presley* is the last two words), or a reversal ("most people aren't paying attention at all").
5. **Loop ending (Elvis):** the last shot matches the first (face on the bathroom floor), so the replay is seamless.

## Visual grammar
- **Every noun gets a picture, at the moment it is said.** Knife → knife close-up, soup → pot, weddings → couple, "tissue" → fin opening into fibres, "camera" → camera.
- **Highlight the thing being named:** glowing outline or colour tint on the object (fin in yellow, shark in red, layers in magenta/green, robot hand in yellow). It's switched on for exactly the words that name it.
- **Make the invisible visible:**
  - x-ray/glass organs (blue = normal, red = failing)
  - cutaway windows through clothes
  - a glowing pulse running along a cable (signal)
  - green wireframe over a hand (computer vision)
  - a pop-up UI card ("ROCK")
  - a clock prop for time
  - a big bold stat graphic (">30 LB")
- **Explainer inserts on a plain cyan studio backdrop:** an isolated object, softly lit, rotating or opening. They're cheap to make and used constantly.
- **Inner-world shifts:** thought or fear becomes a lighting and colour change on the same set (the plaza turns dark blue with a spotlight circle and pointing crowd), entered through a cloud burst.
- **Character acting is big and clear:** facepalm, freeze, hand over mouth, slump, strain, collapse, dramatic falls. Reaction close-ups follow every event (shot/reverse-shot).
- **Lots of angles:** extreme close-up, POV and over-the-shoulder, low angle through table edges, top-down, macro on props, wides for space, and orbiting camera around mechanisms.
- **Captions:** white, bold sans-serif, soft shadow, centred in the lower-middle third, 1–3 words, swapped on word timing. No colour karaoke.
- **Look:** clean stylised CG with saturated cyan/blue backgrounds, glossy materials and strong rim/soft key. This is *more stylised and brighter* than our textured, muted direction. Take the **pacing and grammar**, not necessarily the palette.

## What this means for our pipeline
1. **Script first, timed to the word.** Narration (~2.6–2.9 w/s, 80–115 words for 30–40 s) → word timestamps → every 1–3 words is a beat → shot list. The animation is built to the narration's timing, not the other way round.
2. **Fewer heavy "acted" shots, many cheap shots.** The share of inserts varies: almost none in Spotlight (all acting), about half in Shark and Elvis, most of RPS robot. Inserts are a prop close-up, an isolated object on a backdrop, an x-ray overlay or a UI pop-up. Those cost minutes, not hours. Full-body acted shots (walk, fall, drink) are the expensive ones and should be spent where the story needs them.
3. **Reusable toolkit to build once:**
   - highlight/outline shader with keyed on/off
   - x-ray/glass material
   - studio backdrop scene
   - transition rigs (whip-pan with motion blur, fly-through, push-in)
   - pop-up icon/stat graphics
   - pulse-along-a-path effect
   - automatic captions burned in from word timestamps
   - library of stock actions on our rig (walk, stop, kneel, fall, facepalm, point, laugh, strain, collapse, pick up, drink)
4. **Camera always moving.** Every shot gets at least a slow push, drift or orbit, and transitions are motivated camera moves.
5. **Previews:** at this shot density a CPU-only preview of 35 s at 60 fps is 2,100 frames. Previews need to drop to lower resolution or 30 fps (stepped) for blocking, then one continuous 60 fps pass before the farm.
