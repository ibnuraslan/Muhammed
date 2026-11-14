# The Typewriters That Spied on America — STORYBOARD v2

Sheet: `review/typewriters_storyboard_v2.jpg` (before | after for every changed shot). Full storyboard: `review/storyboard/STORYBOARD_FULL.pdf`.
Motion previews: `review/typewriters_preview_*.mp4`: journey (Ch3 long take), count (Ch1 4B), board (Ch4 8B),
sixdays (Ch2 1B), cover (Ch1 1A, idle life). They're 633×269 at 4 samples, rendered at 12 fps and played at 24 fps (each frame held twice),
so the motion steps a little. The final renders are 24 fps.
Inspiration: the reference breakdowns on `claude/fern-analysis` (`research/refs/`). Nothing is copied from them. The ideas
are the general devices they use: facts made physical, counts as objects, hero objects on black, evidence on a board,
and one long take per chapter.

## Changed shots

| Shot | Old idea | New idea | Why it's stronger |
|---|---|---|---|
| Intro 5A "Copiers. Computers." | Attic: a man pushes a hand truck past rows of crates | **Hero inserts on black**: the camera slides along a dark stage from a copier to a terminal, each in its own hard pool of light, cut on the words | A list becomes one object per word. Each machine is introduced like evidence, not lost in an attic |
| Intro 5B "Encryption machines." | Attic: burlap stapled over a crate | **Cipher machine alone in the light**, its lamps blinking, slow push | Same evidence language, and the cipher box (the thing Washington suspects) gets its own beat |
| Ch1 4B "roughly two hundred and fifty typewriters" | Corridor of office doors | **250 typewriters in rows on a warehouse floor**: top-down on one machine, the camera rises straight up until all 250 fill the frame | The number is shown as the things themselves, with no text. The rise gives it scale |
| Ch1 6B "staples and seals carry microscopic markings" | A worker stapling burlap | **Macro: one staple pressed into the burlap seam**; the camera creeps in under a low raking light until the coded engraving on its crown resolves | A literal action becomes the detail the line is about: the marks are what you see |
| Ch2 1B "six days a week" | A calendar page flips | **Locked-off time-lapse of the test hall**: six days pass in seconds; daylight swells and dies through the blinds, the technicians jump from bench to bench | Time passing becomes light and bodies, not a prop. It reads as labour, not a calendar |
| Ch2 2B "For weeks, they come up empty." | Two men stack crates | **Top-down over the hall floor covered with checked equipment**, each piece with a pale cleared tag; the camera drifts slowly across it | "Weeks" and "empty" in one image: a growing pile of everything they checked, all of it clean |
| Ch3 2A–4A "Underneath... arms... magnets... the electronics sense... once it has enough data," | Five separate macro shots (sink, arms, magnets, X-ray) plus an embassy window at night | **ONE LONG TAKE (Ch3 hero, ~17–24 s)**: from the ball striking the page, down past the keys, under the carrier to the arms as the housing fades to X-ray, along the bar to the hidden board, where eight tiny lights fill up as the data comes in | The explanation becomes one unbroken path that follows the signal. The literal night window is replaced by the board filling up |
| Ch4 8B "The full list... beyond what investigators can reconstruct." | An inspector checks a seal on a dock | **The investigators' cork board**: printed photos of earlier scenes (evidence hall, customs, the attaché's office, the TV tower, the X-ray film), red string already up pin to pin and running on to three empty pins with torn corners; the camera drifts along it and settles on the empty pins | It shows what is known and, in the empty pins, what never will be. It calls back to earlier chapters through the printed photos |

## Long take per chapter (hero shots, held long on the voiceover)

| Chapter | Hero long take |
|---|---|
| Intro | 7A/7B vault: the slow push past the teletype and cipher racks, then the torch sweep, as one held move |
| Ch1 | 11A/11B stairwell: the teletype carried down the stairs, seen from the top of the well |
| Ch2 | 5B the X-ray film on the lightbox: the electronics appear in the film |
| Ch3 | 2A–4A **journey** (new, above) |
| Ch4 | 10B the pull-back from the rooftop aerials to the TV tower |

Around each hero take, the list lines are cut as short inserts on the word: intro 5A/5B, Ch1 7A/7B, Ch3 6B.

## Animation pass

- Every standing person now has idle life: breathing, a slow weight shift, small head turns, each on their own phase.
  This runs off a shot clock that every scene reads (`twp.idle`, `twp.CLOCK`).
- Hands: every reach rolls the palm the right way up (measured on the rig), elbows stay bent, and there are no empty
  mid-air hands. Hand QA crops stay part of every sheet.
- The new shots all move: the camera rises, slides, drifts and pushes; the cipher lamps blink, the daylight cycles and the
  board's lights fill. Nothing moves on its own: the board string and the cleared floor are static (rule 1).
- Unchanged: look v5 (real colours, mood from shadow and contrast), the day-brightness check, a title lead of 3 s or more
  under two-line chapter cards, one film file with PNG output and an audio pair, and a farm-ready master.
