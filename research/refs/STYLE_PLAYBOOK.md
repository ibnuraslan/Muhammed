# Style Playbook — what the reference films do, and what Seldom should adopt

All 8 reference files turned out to be **Fern** films (one channel, several sub-styles). `videoplayback (1).webm` = the Ötzi film (06), so 8 unique films. Fern renders in **Blender** (the UI is shown in film 01's outro), so all of this is reachable with our pipeline.

## Files

| # | Film | Breakdown | Contact sheet |
|---|---|---|---|
| 01 | How the Secret Service Works | `01_fern-secret-service.md` | `.jpg` |
| 02 | NATO's Plan If Russia Attacks Tomorrow | `02_fern-nato-russia.md` | `.jpg` |
| 03 | How an FBI Agent Infiltrated the KKK | `03_fern-fbi-kkk.md` | `.jpg` |
| 04 | The ancient computer that shouldn't exist (Antikythera) | `04_fern-antikythera.md` | `.jpg` |
| 05 | The Only Nazi Hitler Feared (Heydrich) | `05_fern-heydrich.md` | `.jpg` |
| 06 | How an Ancient Mummy Changed History (Ötzi) | `06_fern-otzi-mummy.md` | `.jpg` |
| 07 | The Mutated Animals of Chernobyl | `07_fern-chernobyl-animals.md` | `.jpg` |
| 08 | The 13-Year Investigation Into Flight 103 | `08_fern-lockerbie-flight103.md` | `.jpg` |

## Style comparison

| # | Length | Designed visuals | Median shot (3D) | Longest hold | People style | Signature device | Palette |
|---|---|---|---|---|---|---|---|
| 01 Secret Service | 27:12 | 65% | 3.8 s | 42 s | Stylised-real faces, ECU hands/eyes | Fictional present-day plot as spine | Night, single red/blue rim |
| 02 NATO | 17:32 | 63% | 4.3 s (maps 9 s) | 56 s map | Few people, hooded | One map system, "follow one asset" | Dark grey + teal/red map |
| 03 FBI/KKK | 41:04 | 66% | 4.3 s | 62 s | Realistic main character, criminals as sketches | Witness interview drives the 3D | One palette per "world" |
| 04 Antikythera | 14:43 | 92% | 6.3 s | 44 s | **Grey clay statues** | Photoreal hero object | Navy + bronze, cyan X-ray |
| 05 Heydrich | 18:50 | 70% | 5.3 s | 40 s | Heroes realistic, villain only silhouette | Archival photos as desk props | Sepia paper + red light |
| 06 Ötzi | 11:53 | 85% | 3.4 s | 83 s | One groomed character | One hero model in 30+ shots | Cold blue vs warm body |
| 07 Chernobyl | 17:51 | 79% | 11.5 s | 90 s | Animals as protagonists | Science on black, footage in "cards" | Green-grey fog, toxic yellow |
| 08 Lockerbie | 28:05 | 60% | 4.4 s | 56 s | Investigator duo, silhouettes | Cork board with red string | Grey maps, night blue, red suitcase |

## Patterns in all 8 films

| Area | Rule |
|---|---|
| Cold open | 30–90 s of pure 3D, mid-action, with a date/time/place tag. Real stakes in the first sentence. Often a teaser montage of later scenes |
| Shot length | 3D shots 4–6 s median, but **every film has 30–90 s single takes** at its key moments. Archival is cut 2× faster (1.5–3 s) |
| VO → shot | Lists = one short shot per item, cut on the word. Paragraphs = one long, slow move |
| Abstract facts | Never bullet slides. Always a physical thing: a printed photo, a map with a red line, text written in the 3D room, a dot grid, an object on black |
| Real people | Rarely a realistic 3D likeness. Instead: silhouettes, back views, clay figures, pencil sketches, framed archival photos |
| Camera | Slow pushes, top-down for space/logistics, macro on hands/eyes/objects, symmetric frontal shots for institutions |
| Light | Dark scenes, one dominant source (torch, spot, window, rim). Red = danger/evil, used sparingly |
| Labels | Small, consistent: name + role, date tag, place tag. "Abstract/simplified visualization" when needed |
| Structure | Ring structure (end where it began), recurring hero objects/sets, callbacks |
| Chapters | Short card: number + one-line title, over a frame from that chapter or in a small box |

## Top 10 techniques for Seldom to adopt

Our style: realistic 3D in Blender Cycles, look v5 (real colours, mood from shadows and contrast, no teal/grey), MakeHuman characters, `title_card.py` two-line chapter titles, documentary VO.

| Rank | Technique | Seen in | Pipeline change | Effort |
|---|---|---|---|---|
| 1 | **Faceless or stylised people for real persons**: silhouettes, back views, or grey clay figures; realistic faces only for 1–2 leads | 03, 04, 05, 08 | `look.py`: add a `clay` material preset (grey, roughness 0.6) for MakeHuman meshes, plus a "silhouette" lighting preset (hard backlight, no fill) | Easy |
| 2 | **Physical facts**: archival photos printed on a desk, vintage maps with red lines, text written into the 3D set | 01, 05, 06, 08 | New `props_lib`: photo-print plane (paper bump + curl), cork board + red string, wood desk, typewriter date card. `fact_text()` helper for text on walls | Easy |
| 3 | **One long take (30–90 s) per chapter** at the emotional peak; short inserts around it | all | `chapter_shots.py`: each chapter gets 1 `hero_long` shot (slow push, 30–60 s) + N inserts of 1.5–4 s; cut lists on word timestamps | Easy |
| 4 | **Cold open with a date/time/place tag + 30–40 s teaser montage** | 01, 03, 05, 08 | `title_card.py`: `place_tag(date, time, place)`; edit rule: teaser from renders of later chapters | Easy |
| 5 | **Recurring hero objects and sets** (suitcase, mummy, cork board) used as callbacks and in the ending | 04, 06, 08 | Build 3–4 hero assets per film, render each in several chapters; end the film on the opening set (ring structure) | Medium |
| 6 | **One map design system**: dark land, one route colour, pill labels, long holds (10–50 s) | 02, 05, 08 | `map_style.py`: shapefile → curves, ortho camera, real-colour palette (e.g. charcoal land, brick-red route, cream labels); relief variant with displacement | Medium |
| 7 | **Object-on-black product shots** with one hard top light for evidence and hardware | 02, 04, 07, 08 | `look.py`: `void_spot` preset (black world, 1 area light above, glossy floor fade). Fits look v5 contrast rule | Easy |
| 8 | **Count/scale as physical units**: dot grids, icon grids, toy soldiers, measurement line in 3D ("4.5 m", "20 mi / 32 km") | 01, 02, 05, 08 | Geometry Nodes `dot_grid(n, highlight)`; `measure_line(a, b, label)` helper | Easy |
| 9 | **One palette per "world"** inside one film (torch, fluorescent, window-blue, golden hour), all practical-light driven | 03, 06 | `look.py`: named mood presets per chapter, still real colours; practical lights (flicker driver) + volumetric haze | Easy |
| 10 | **Honesty tags + framed real evidence**: "Simplified visualization" tag; real footage in rounded cards so it never mixes with 3D | 06, 07, 08 | `title_card.py`: `viz_tag()`; card-carousel frame template for archival | Easy |

## Already in Seldom vs gap

| Area | Seldom now | Gap to close |
|---|---|---|
| Render look | look v5: real colours, contrast-driven mood | Add void/spot, clay, silhouette and practical-light presets (#1, #7, #9) |
| Chapter titles | `title_card.py` two-line titles | Render over a live frame from the chapter (01); add date/place/name/viz tags (#4, #10) |
| Shot planning | `chapter_shots.py` | Long-take rule + list-to-inserts on word timestamps (#3) |
| Characters | MakeHuman, realistic | Use realism only for leads; clay/silhouette for everyone else (#1) |
| Facts/data | (per film) | Physical props library, maps system, dot grids (#2, #6, #8) |
| Structure | Documentary narration | Cold-open teaser, recurring hero objects, ring ending (#4, #5) |

## Avoid / costly

| Item | Why |
|---|---|
| Fur/groomed humans and animals in close-up | Very render-heavy; Fern uses them sparingly (Ötzi, goat, deer) |
| Aircraft/vehicle destruction sims | Cell fracture + rigid bodies on big models: high cost for seconds of screen time |
| Dense crowds in focus | Use DOF and silhouettes as Fern does |
| Teal/grey grade | Fern's maps lean teal; we keep real colours and get mood from shadows |
