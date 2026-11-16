# SafetyPin v002b (B20, "This invention made millions")

Built to the client VO (`SafetyPin_v002b_VO.mp3`, word frames in `beats.json` / `vo_words.json`). Every shot is a 1× slice of its
animated clip (no time-stretch); shot cut table: `../SafetyPin_v001/scripts/segs.json`.

| Beat | Frames | VO |
|---|---|---|
| B1 wire → coil spring | 1–331 | He bent a piece of wire into a coil, creating a spring that allowed it to open and close. |
| B2 clasp | 332–538 | Then he added a simple clasp to cover the sharp end. |
| B3 straight pins hurt | 539–872 | Before this, people commonly used straight pins, which could easily stab them and cause infections. |
| B4 first modern safety pin | 873–1123 | His design solved that problem and became the first modern safety pin. |
| B5 $15 debt | 1124–1343 | But he desperately needed money to pay off a $15 debt, |
| B6 sold the patent | 1344–1529 | so he sold the patent for only $400. |
| B7 made millions | 1530–1663 | The safety pin eventually made millions, |
| B8 died with little money | 1664–1857 | while its inventor died with very little money. |

DA KRAS FILMS logo: the two front pin boxes in 7a/7b (1530–1663). No other text on screen (patent, debt note, banknotes, newspaper are blank line art).
Build: `../SafetyPin_v001/scripts/` (01_chars → 02_sets → 03_anim (+anim_b3_b8) → 04_lights → anim_look → 05_vo_cut → 06_pack).
Review: `review/preview.mp4` (every 5th frame, 270×480, with VO) and `review/pages/`.

## v002b (director fix round, from v002)
- Friend re-cast on a clearly male donor with a loose suit (EscapeArtist `Judge`, the TenDimes "Singer" rig): green jacket, light shirt, blond-tinted hair, eye fix (cornea kept transparent: the old fallback made his eyes white).
- B5 (1124–1343): the inventor sits slumped forward with his arms hanging down to his knees, elbows in at his sides (no hands-on-hips). For B5 only the bench and its dressing sit 20 cm further away so his arms clear its edge; 5b insert re-aimed to the moved note.
- Re-rendered preview range 536–1343 from this exact package and spliced into review/preview.mp4; nothing else changed.
