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

---

# Batch 02 (5 more videos): what's new

Videos: two-headed cows (44.3 s), sand at light speed (35.9 s), diver swallowed by shark (27.5 s), viral video gets man a job (30.5 s), dead cat strategy (30.0 s).

| | Cows | Sand | Shark diver | Viral job | Dead cat |
|---|---|---|---|---|---|
| Words / speed | 125 / 2.88 w/s | 88 / 2.51 | 85 / 3.19 | 88 / 2.96 | 68 / 2.34 |
| Narration starts | 0.00 s | 0.00 s | 0.00 s | 0.00 s | 0.00 s |
| Near-static picture | 0.7 s | 0.1 s | 0.4 s | 0.0 s | 0.2 s |

**Across all 10:** narration always starts at 0.00 s, 2.3–3.2 words/s, 27–48 s long, under ~1 s of still picture per video (one outlier at 2.6 s).

## Hook types (first line)
- **Hypothetical:** "If a cow is born with two heads…", "If you took one grain of sand…"
- **True story mid-action:** "He was collecting shellfish when…", "He was leaving a job interview when…", "He slammed a dead cat onto the table…"
- **You-POV** (batch 1): "A pretty girl waves at you."

## New techniques
- **Porthole cutaway:** a circular window opens in the animal's body to show the organs inside, while the animal stays in its environment (cows). Directly useful for animal stories.
- **Abstract interior backdrop:** internal processes (egg splitting, embryo growing) play on a plain deep-red "womb" backdrop instead of a modelled interior. Cheap and clear.
- **Literal punchline prop:** "never live past their second birthday" ends on a birthday cake with a "2" candle.
- **Lighting carries meaning:** sunny farm while the calf struggles, dusk tones for "grows weaker".
- **Animated numbers and HUD graphics:** a speed counter rolling up to "186,000 mi/s", speed lines, a battery-charge icon, a VHS-style "REWIND" overlay to reset a hypothetical.
- **Human anchor before the abstract:** the sand video starts with a person holding a grain with tweezers before going cosmic.
- **Continuous action chase:** the shark-diver story flows as almost one unbroken camera move. The glowing highlight hits the vest and the chisel exactly when named.
- **Phone screens as story devices:** a viral video playing on a phone with a rising view counter, an incoming call card, stacked job-offer notifications.
- **3D title card:** the concept name ("DEAD CAT STRATEGY") as big extruded text next to the object, once, mid-video.
- **Visual metaphor ending:** "slips by unnoticed" is a newspaper headline blowing away down an empty street.
- **Extreme close-up on the eyes** for "realize it".

## Look
The Viral-job and Dead-cat videos are **realistic and moody**: grey streets, brick, practical lights, real-world materials. The Cows video is a realistic farm with grass, fences and a barn. These are much closer to your textured, grounded direction than batch 1's glossy cyan style. The channel's *look* varies by topic; the *pacing* never does.

## Caution
They show real brand logos (a restaurant chain sign). We should use invented brands to avoid trademark trouble.

---

# Batch 03 (5 videos, 4 new; one repeat of Shark Finning)

Videos: Roman sailors' desalination (24.8 s), DIY faucet sprayer hack (32.1 s), two kids & the bike, a parable (52.5 s), blind quarterback (34.8 s).
**Delivery spec confirmed** from the native files: **1080×1920, 29.97 fps**. Earlier copies were 720p re-uploads.

| | Roman water | Faucet hack | Bike parable | Blind QB |
|---|---|---|---|---|
| Words / speed | 68 / 2.82 w/s | 92 / 2.93 | 137 / 2.66 | 92 / 2.71 |
| Near-static picture | 0.2 s | 0.4 s | 0.2 s | 1.4 s |

## New formats
- **Historical "how they did it":** warm, firelit realism (wooden ship, brass pot, open fire). This is the closest to your Goat Rescue look so far.
- **DIY hack + twist:** a hands-only tutorial on a cyan backdrop, then a "but…" downside (bacteria macro → "germ fountain").
- **Parable / moral (52 s):** two characters on parallel tracks, intercut, ending on a moral line. The longest video and still never static.
- **Inspirational true story:** a disability overcome, ending in a triumphant wide shot with a crowd.

## New techniques
- **Time passing as a prop:** a jar labelled "Bike" filling with coins ("months passed"), and a "5 Year" circular-arrow icon for time jumps. The character also ages across shots (toddler → kid → teen → adult) for a life story.
- **Thought bubbles:** cartoon cloud bubbles showing what a character wants (the bike, a pile of money).
- **Mental image as a hologram:** "helping him picture where everyone was" is shown as blue neon wireframe players on black. The same trick as the "inner world" in batch 1.
- **Invisible signals drawn as beams:** the walkie-talkie voice travels as a cyan beam into the helmet. A glowing brain inside the helmet stands for "from memory".
- **Measurement props for physical states:** a digital thermometer insert for "once it cooled", and the sponge changing colour as it absorbs.
- **Cross-section cutaways of objects,** not just bodies: a bottle cap with sponge inside, and an eyeball with tumours inside a porthole vignette.
- **Repetition montage:** the same action with different partners (carrying backpacks, giving away lunch) to show "every day".
- **Happy-ending reaction:** characters smiling with thumbs up, or a crowd cheering. Endings resolve emotionally, not just factually.

---

# Synthesis (15 videos): production template for one piece

| Item | Target |
|---|---|
| Length | 25–50 s (most 30–35 s) |
| Script | 70–140 words; ~85–95 for 30–35 s. Delivered at 2.6–2.9 words/s with no gaps over ~0.5 s. |
| Line 1 | The hook, already mid-action, in one of four forms: true-story action ("He was…when…"), hypothetical ("If you…"), you-POV ("A pretty girl waves at you"), or instruction ("Poke the hot nail…"). |
| Structure | Hook → mechanism / what happened → "You see" / "But" turn → payoff line with consequence, reveal, moral or twist |
| Captions | 1–3 words, white bold, lower-middle, on word timing |
| Camera setups | A new one every ~1.5–2.5 s (about 15–25 per 30–35 s) |
| Transitions | Motion only: whip-pan, fly-through, push-in, zoom-blur, wipe, flash |
| Still time | Under ~1 s for the whole video |
| Each beat | Shows the exact noun being said, often with a highlight on it |
| Shot mix | Acted character shots, prop/hand macros, explainer inserts on a plain backdrop, cutaways/x-ray, graphics (numbers, icons, phone/UI, time jumps), inner-world/hologram shots |
| Ending | Last word ≈ last frame; loop or callback where possible |
| Audio | Narration on top for the full length, over a continuous sound bed. Pauses between words sit only 5–12 dB below the voice (about −17 to −25 dBFS vs −12 to −15 for speech), so music and/or ambience runs underneath. The tail after the last word peaks at −8 to −13 dB, which suggests sound-effect hits. Measured, not listened to: whether it's music, SFX or both still needs a human ear. |
