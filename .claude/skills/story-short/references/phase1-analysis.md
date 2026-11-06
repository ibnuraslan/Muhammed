# Phase 1: Analyse the script

Goal: by the end of this phase you know the story cold, you know what everything in it
really looked like, and you have far more scene ideas than you'll use.

Inputs: `script.txt`, `timings.txt` (from `--timings-only`).
Output: `projects/<slug>/01-analysis.md` (use `templates/analysis.md`).

## Step 1: Read it like an editor

Write down:
- **Logline:** one sentence. "A young engineer leaves gaps in a railroad and everyone mocks him."
- **The hidden fact / twist:** the real reason that part 2 will reveal (rails expand in heat,
  square windows crack from metal fatigue...). The whole of part 1 is built to make this land, so
  plant visual hints of it (heat shimmer, a stressed corner) without giving it away.
- **Part:** is this part 1 (ends on a cliffhanger) or part 2 (reveal + payoff)? Part 2 needs
  callback shots that mirror part 1's shots.
- **Tone:** comedic? tense? triumphant? It decides lighting and pace.

## Step 2: Beat map (use the real timings)

From `timings.txt`, list every line with its start-end time and label its beat:

| Beat | Typical line | What the viewer must feel |
|---|---|---|
| HOOK | "He sawed gaps into a railroad every 39 feet." | "wait, what? why?" (strange action, shown big) |
| SETUP | "You see, two companies are racing..." | stakes: scale, speed, competition |
| HERO | "He's the youngest engineer on the job." | likes him: calm, clever, underdog |
| CONFLICT | "...his boss sees... his face goes purple." | tension: comic anger |
| VOICE LINE | "You're wrecking my railroad!" | punchline: close-up, character talking |
| STAND | "But he won't close a single one." | respect: hero is stubborn and calm |
| RIVAL WINS | "The other company... finishes first." | injustice: rival is smug, crowd cheers |
| MOCKERY | "...newspapers start calling it..." | sympathy: hero alone, laughed at |
| CLIFFHANGER | "Then summer comes and something weird happens." | dread and curiosity: an ominous change |

Note which words carry weight (numbers, names, insults, verbs of action). Those are the
words to cut on in phase 2.

## Step 3: Research (actually do it)

Use **WebSearch** (standard mode, several queries in one turn) and WebFetch where useful:
- **The facts:** what really happened, the real numbers, the real reason (for the twist).
- **The era and place:** year, country, landscape, weather, light.
- **What things looked like:** vehicles, machines, buildings, tools, uniforms, signage,
  newspapers, interiors. Note shapes and colours you can build from boxes, cylinders and
  canvas textures: "1950s jetliner: 4 engines buried in wing roots, cheatline stripe, round
  nose".
- **Sensory details:** sounds, textures, typical colours of the setting. These become
  texture and palette choices.

Write findings as short bullets with the source. Mark anything uncertain. Story beats can be
dramatised, but don't invent facts and present them as true.

## Step 4: Cast mapping

Map every person in the script to the recurring cast in `style-bible.md`:
- protagonist → **Hero**; authority who objects → **Boss**; competitor → **Rival**;
  everyone else → **extras** (crowds, workers, passengers, reporters).
- Decide era/role adjustments allowed by the bible (e.g. Hero gets a hardhat on a
  construction site, but keeps his signature look).
- New recurring person needed? Propose a design in the bible format and flag it to the user.

## Step 5: Idea dump (quantity first)

For **every line**, write 2-4 visual ideas. Then add a separate list of at least
**5 "crazy" ideas**, the shots people replay:
- impossible camera moves: fly *through* a window, ride on a rail at 2 cm height, orbit a
  falling object, pull back from a close-up to a huge aerial reveal
- scale gags: a tiny hero next to a giant machine, an enormous crowd
- physical comedy: the boss's head inflating red, steam, table bouncing, hat flying off
- visual metaphors: money raining, a clock spinning, a newspaper spinning into camera, a map
  with a racing line
- cutaways / x-ray: see inside metal and show stress lines glowing
- time tricks: freeze-frame, time-lapse sun, slow-motion crack

Also list **visual metaphors for abstract lines** ("gets the whole country's business" → a
map of the country lighting up with the rival's colour).

## Step 6: Sets and props needed

Two lists: **already in the engine** (check `engine-api.md`) and **to build**. For each set to
build, describe it as primitives: "railroad: ground plane + 2 long box rails + tie boxes
every 0.7 m + gravel noise texture; canyon walls = big boxes with striped rock texture".
Prefer generic, reusable sets (`railroad()`, `canyon()`, `kitchen()`) over one-off ones.

## Done when
- [ ] Logline, twist and tone written
- [ ] Every line has a beat label, time range and 2+ visual ideas
- [ ] At least 5 crazy ideas
- [ ] Research bullets with sources for facts and for the look
- [ ] Cast mapping, plus sets/props split into existing and to-build
