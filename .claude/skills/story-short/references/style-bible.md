# Style bible

The fixed look of the channel. Every episode follows it, so viewers recognise the show
instantly. Change it only when the user asks, and log the change at the bottom.

## Format
- 1080×1920, 30 fps, 30–60 s. Part 1 ends on a cliffhanger; part 2 reveals and pays off.
- Captions: Montserrat ExtraBold, white with a black outline and a soft shadow, 1–3 words (≤ 12
  characters), centred at 70% of the height, spoken case (not all caps). These are the
  `make_short.py` defaults; don't change them per episode.
- Look: stylised 3D sets (toon shading, rich saturated colours, simple shapes, canvas-painted
  textures) with flat 2D cartoon characters drawn in thick black ink. The final encode adds
  saturation ×1.22, contrast ×1.06 and a soft vignette (done automatically).

## Team colour codes (most important rule)
Every story has sides. Colour tells the viewer whose side anything is on, at a glance.

| Side | Primary | Secondary | Used on |
|---|---|---|---|
| **Hero's side** | Teal `#169e8f` | Mustard `#e8a630` | his company's logo, vehicles, stripes, signs, counter, flag |
| **Rival's side** | Red `#c8302e` | Maroon `#7b1e2e` / gold `#e0b33a` | rival company, vehicles, signs, confetti bias |
| **Authority** (boss, officials) | Navy `#27345a` | Red tie `#d4352b` | suits, offices |
| **Neutral crowd** | anything from the extras palette | | extras never wear pure teal or pure red |

Company names are invented, short and all caps (SKYWARD vs JETLUX). Pick new ones per story,
but keep the colours.

## The recurring cast
Characters are flat 2D: a big round white head with an 8 px black outline, a simple dot-eye
face, a rounded body, and thin black stick arms and legs.

### Hero, "the Tinkerer" (`new Char(S, 'hero')`)
- **Signature (never changes):** round wire glasses · messy brown tuft hair `#6b3f1f` ·
  pencil behind the ear · mustard vest `#e8a630` over a light-blue shirt `#d9ecfb`.
- Default face: calm, confident half-lidded eyes (`eyes:'half'`) with a small smile.
- Personality: quiet, stubborn, always right in the end. Never angry or shouting. Under
  pressure he crosses his arms and smiles. When mocked: `brow:-0.6, mouth:'flat'`.
- Era/role variants allowed: a hat **on top** of the signature look (hardhat on site, engineer's
  cap on a railroad, chef hat in a kitchen). Glasses, vest and pencil always stay.
- ⚙️ Open question for the user: should the Hero have a permanent cap/hat as part of his
  signature? (default: no hat)

- **THE INVESTIGATOR (`'detective'`): the MAIN CHARACTER of every investigation / horror / crime video**
  (approved by the user 2026-11-08). He presents the case, works the evidence board, visits the places.
  Look: brown fedora with a dark band · round wire glasses · small ears on both sides · a yellow pencil
  with a pink eraser tucked **behind** his ear (only the eraser end shows, never stuck into the head) ·
  beige trench coat, open, over the mustard vest and light-blue shirt · coat belt with a brass buckle.
  **No beard, no moustache.** Default expression: calm, half-lidded, slightly frowning (`eyes:'half', brow:0.3`).

### Boss (`'boss'`)
- Bald with a three-strand comb-over · huge white walrus moustache · bushy grey brows ·
  wide navy suit · red tie. About 7% taller than the Hero (`h: 2.15`).
- **Signature gag:** anger ramps his face white → red → purple, then steam puffs (`anger` 0→1,
  `steam`). Slams tables, shouts with `talk:1` (his mouth becomes a shout).

### Rival (`'rival'`)
- Slick black hair with a shine · square black sunglasses · pencil moustache · maroon suit,
  gold tie. Tall and thin (`h: 2.2`). Default `mouth:'smirk'`.
- Arms spread wide when showing off. Never looks worried in part 1.

### Extras (`new Char(S, 'extra', { seed, hat, color })`)
- Random but deterministic from `seed`. Hats: pilot, beret, bun, hair, cap, hardhat, none.
- Crowds: 6–18 people, with a mixed `facing`, all reacting together (cheering = `eyes:'happy',
  mouth:'grin'`, arms up and hopping).

## Expressions cheat-sheet
| Emotion | Pose |
|---|---|
| confident | `eyes:'half', mouth:'smile'` |
| happy / cheering | `eyes:'happy', mouth:'grin'`, arms 2.4–2.8, `hop` |
| shocked | `eyes:'wide', mouth:'o'`, `sweat:1`, little `hop` |
| angry | `eyes:'angry', brow:1, anger:0.8, mouth:'frown'` → `'shout'` |
| furious | `anger:1, steam:1, talk:1` |
| sad / mocked | `eyes:'dot', brow:-0.6, mouth:'flat'`, arms down |
| smug | `mouth:'smirk'`, arms spread `2.3` |

## Lighting presets
- **Day exterior:** `S.sky({ top:'#2f6fd6', horizon:'#cfe6ff', sun:[-60,70,50] })`
- **Interior (office):** `S.sky({ hemi:1.5, fog:null, sun:[-20,30,40], shadow:15 })`
- **Golden hour / ominous:** `S.sky({ top:'#1f3f88', horizon:'#ffb78a', sunColor:0xffc890, sun:[-80,40,20] })`
- **Hangar / big interior:** `S.sky({ top:'#4a86e0', horizon:'#ffe2b8', hemi:1.5 })` + a point light
- Night (not built yet): deep navy sky, warm practical lights, more contrast.

## Camera language
- Every shot moves. Default `ease.io` push or pull of 15–30%. Cliffhangers use a slow push and a tiny shake.
- Low angles for power (boss, rival, machines). High angles for loneliness (hero mocked).
- Fov 40–56. Wider is for interiors and crowds.

## Change log
- 2026-11-08: the Investigator (detective) is the main character for investigation videos; ears added, pencil moved behind the ear.
- 2026-11-06: bible created from "The Round Windows" (example episode).
