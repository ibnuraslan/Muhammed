# SwedishCoffee: PLAN (checkpoint A)

Connect27 · branch `claude/connect27-swedish-coffee` · 1080×1920 · 60 fps · frames 1–2670 (44.5 s) · Cycles CPU · AgX Medium High Contrast

## Concept for one camera
The whole film is one "camera ride" through a single connected 18th-century Swedish world built along a long path (a street that runs from the execution courtyard, into the palace, through the castle chamber, out to the church and back to the square). Every set change is a physical move: through a doorway, through a window, through coffee steam, a whip-pan along a corridor, or a crane up through a ceiling/chandelier. Time passing (beat 8) happens in place: lighting, candles and the twins' age change while the camera orbits.

Characters are MPFB2 humans (MakeHuman CC0): **Twin A / Twin B** (one identical phenotype, two copies; aged with the MPFB age slider in later beats, i.e. separate "old" copies swapped while hidden behind foreground or steam), **King** (wig + ermine cape built as cloth-sim/displaced fur over MPFB body), **2 guards, 2 doctors, 2 servants, crowd ~12** (variant phenotypes, low subdiv). Period costume: MPFB suits retinted (dark wool, linen) + modelled coat tails/waistcoats with real cloth textures; tricorn hats from Sketchfab if found, else sculpted. Faces driven with MPFB face bones (brows/lids/jaw/lips) on every emotional beat.

## Beat table (frame = round(t·60)+1)
| # | t (s) | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|
| 1 | 0.0 | The twins were about to be executed | Cobblestone courtyard (Poly Haven cobble + castle wall scans), timber scaffold, two identical shackled young men led up the steps by guards, crowd jeering, banners-free, pigeons/dust, drum. | 0.0 wide high over crowd → 1.0 push in over heads → 2.0 low close on shackled hands/faces (fear brows) |
| 2 | 2.8 | the king suddenly stopped it | Rider/herald bursts in? No — reveal: camera whips left up the palace façade and through the open throne-hall window: King on throne in powdered wig + ermine raises his hand; a guard sprints out the door past camera. | 2.8 whip-pan up façade → 3.4 through window → 4.0 medium king, hand up (angry brows) |
| 3 | 4.9 | hated coffee… convinced it was poison | King leans over a side table to a steaming porcelain coffee cup; glare (brows down, lip curl). Steam (volumetric smoke sim) curls into a skull shape (skull mesh used as a smoke emitter/density field; no text). | 4.9 push to close on face → 6.0 orbit to cup over shoulder → 7.0 macro cup, steam rises → 8.0 tilt up with steam, skull forms → 9.0 pull back through steam |
| 4 | 9.7 | banned it across his kingdom | Exit through steam into a street: soldiers smash coffee pots (rigid-body shards), a sack of beans pours into the gutter (particles), townsfolk protest with raised arms, a cart, shutters. | 9.7 emerge from steam high → 10.5 dolly low along gutter with beans → 11.3 rise past a protester |
| 5 | 12.0 | instead of killing them | Fly through a castle-chamber window: twins seated at an oak table, guards behind, light shafts, a clerk at the door. | 12.0 through window → 12.8 slow arc to front of table |
| 6 | 13.7 | three pots of coffee every day | Twin A drinks cup after cup of black coffee; servants pour from silver pots (liquid stream mesh), a row of three pots; empty cups stack up. | 13.7 orbit begins at twin A → 14.7 macro pour → 15.7 orbit past servant → 16.7 close drink → 17.6 three pots in frame |
| 7 | 18.3 | the other drank three pots of tea | Continue orbit to twin B with fine porcelain teapot and cups, sipping politely, pinky out. | 18.3 orbit onto B → 19.3 macro porcelain pour → 20.5 close on B sipping |
| 8 | 21.6 | Two doctors watched them for years | Two elderly doctors at a desk with quills and blank-paged ledgers observe; time-lapse: candles burn down (shape keys), window light cycles day/night, seasons outside (leaves → snow), twins swap to older copies under a light flash. | 21.6 pull back over doctors' shoulders → 23 crane around desk, candles shrink → 24.5 window seasons → 26 twins older, push in |
| 9 | 27.4 | both doctors died first | Through the window, out to a stone church in snow; two coffins carried by pallbearers; older twins follow in black. | 27.4 fly out window → 28.4 descend to procession → 29.5 track alongside coffins → 30.5 twins' faces |
| 10 | 31.1 | the king was assassinated | Up and into the palace ballroom: masked ball, candle chandeliers, dancers turning; pistol muzzle flash from behind a masked figure (silhouette, no detail), king collapses (no blood), dancers scatter. | 31.1 crane up through chandeliers → 31.9 dolly behind masked figure, flash → 32.5 king falls, camera drops |
| 11 | 33.3 | the tea-drinking twin died | Through doorway into a bedroom: old twin B lies peacefully in a four-poster bed, eyes closed; old twin A sits at his side holding his hand; candle, rain on window. | 33.3 drift through door → 34.5 slow arc over bed → 36 close on held hands |
| 12 | 37.1 | the coffee drinker as the last survivor | Pan to the window seat: very old twin A sipping coffee, smiling (cheeks/lids), sunlight. | 37.1 orbit to window → 38.5 close smile → 40 over shoulder through window to square |
| 13 | 41.7 | the ban on coffee was lifted | Out the window into the town square: stalls reopen, steam from kettles, people toast with cups, children run, birds. Crane up and settle. | 41.7 fly out → 42.7 through stalls → 43.6 crane up and settle |

`beats.json` will carry these 13 start frames for `retime_to_vo.py`.

## Sets & assets (licences)
- **Poly Haven (CC0):** HDRI (overcast + interior), cobblestone, castle wall / rough plaster, oak planks, wood floor, marble; possible models (wooden table, chairs, candles, lanterns, barrel, crates).
- **Sketchfab via Objaverse (CC-BY/CC0, credited):** searching now: coffee pot, silver teapot, porcelain cup, throne, table, chair, coffin, four-poster bed, chandelier, scaffold, church, market stall, candle, quill, book, venetian mask, baroque building, tricorn hat, flintlock pistol (silhouette only, no detail).
- **MPFB2 / MakeHuman (CC0):** all people. Shirt prints patched out; no text anywhere (ledgers blank/scribble-free).
- Procedural only where nothing exists (scaffold timbers, ermine cape, wig curls): displaced/textured to photo level.

## Tricky shots and plan
1. **Skull in steam (b3):** Mantaflow smoke from a cup emitter; a skull mesh inside the domain as a density source + force guide for ~1.5 s, then dissolving. Fallback: volume shader with skull-shaped density (mesh-to-volume + noise) blended in the steam.
2. **Time-lapse + ageing (b8):** two MPFB copies per twin (young age 0.5, old age 0.9); swap hidden behind candle flare/foreground occluder. Candle shape keys, window light keyframed, season card outside window.
3. **One camera through 6 sets:** sets laid out on one map with doorway/window portals; camera on a single Bezier spline with follow-path + eval-time keys (goat_rescue2 pattern). Wall passes ≤6 frames with textured macro detail.
4. **Assassination (b10):** dancers on simple walk/turn cycles; masked figure from behind, point light flash + smoke puff, king ragdoll-free keyed collapse with planted contacts. No weapon detail, no blood.
5. **Liquids:** pour streams as animated curve meshes with glossy dark coffee / amber tea shader; cup fill levels via scaled liquid disc.

## Schedule (UTC)
A 22:13 plan · B 23:45 blocking 1 still/s · C 01:15 polish 0.2 s sheets + audit · D 02:15 package `blender/SwedishCoffee_v002/` < 95 MB, normal git file, **no LFS** (Batch 2 rule overrides the brief's LFS line).
