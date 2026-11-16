# B26 TenDimes: plan (v002, built to the client VO)

Vertical 1080×1920, 60 fps, Cycles. 22 shots, hard cuts (one camera per shot, switched by timeline markers).
Scripts: `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` → `pipeline/anim_look.py` (see README).
Each shot is a 1× clip about 30% longer than its expected beat, so it can be trimmed to the VO without stretching.
Phase-1 timeline: clips back to back, frames 1–2784 (`build/timing_used.json`). In Phase 2, `03_anim.py -- timing.json` lays the shots to the VO frames.

Reference (`B26_TenDimes_reference_1fps.jpg`, current style): the shot order, subjects and framing follow it: singer on a red-curtain stage → dimes → the son taken at home → payphone, handset, coins → anxious face → two days later, reunion on a suburban street by a black car → face close-ups → dimes "for life" → burial, daughter, dimes.

## Cast (MPFB rigs re-used from our delivered packages, re-dressed; generic faces, no likeness)
| Character | Source rig | Dress |
|---|---|---|
| Singer | EscapeArtist `Judge` | light-grey 1960s suit (luminance-mapped), white shirt, striped tie, modelled grey fedora (tapered crown, plain dark band, narrow brim, tipped back so the eyes read; head bone), navy pocket square, black shoes; hair cards trimmed at the right ear (handset) |
| Son (young adult) | DonationBin `Shover` | striped shirt, jeans |
| Kidnapper | EscapeArtist `Guard2` | charcoal shirt and trousers, bare head (face readable) |
| Daughter | DrunkTrain `WitA` | black blouse and skirt, dark bob with the fringe trimmed off the eyes |

All four have the eye fix (EnhancedEye cornea → transparent mix), a camera-carried catchlight in every shot, the elbow IK limit opened (−40°…145°), hand limits, and relaxed hand presets.

## Sets (one scene, laid out along X)
| Set | X | Contents |
|---|---|---|
| CLUB | 0 | plank stage, pleated red velvet curtain, gold valance, stand mic (CC-BY), small side table with a glass, hall tables with lamps |
| ROOM | 30 | light-blue walls, door with frame (swings open), hallway behind it (lit), window with sky, bed (CC-BY), plant, chair |
| STREET | 60 | red-brick wall, wall payphone (CC-BY, re-surfaced plain metal because its texture had printed text; a clean modelled handset for the held shots), coin ledge, pavement, kerb, road, tree, **club poster with the DA KRAS FILMS logo** |
| SUBURB | 90 | lawn, pavement, house facades (CC-BY), black 1950s car (CC-BY, recoloured), trees |
| CEMETERY | 120 | lawn, gravestones (CC-BY), closed dark-wood casket on a draped dark plinth with a folded cloth skirt, flower spray, trees |

## Shots
| Shot | ~s | VO (expected) | Who / action | Camera | Risk → safe staging |
|---|---|---|---|---|---|
| S01 | 2.0 | "The singer…" | Singer at the stand mic singing (jaw), sway; right hand rises into an open-palm gesture | MS, front-right, slow push-in | mic not over the face (3/4 angle) |
| S02 | 1.6 | "…always had ten dimes" | Ten dimes on his side table; he looks down at them, behind | close on the table, push-in, singer's jacket behind | **no grip**: dimes rest on the table (LESSONS §2.1) |
| S03 | 2.0 | "And the reason for this is kind of sad" | CU singing, eyes lower, head tilts | CU front-left, push-in | mic kept >0.9 m from the lens |
| S04 | 1.5 | "You see, his son…" | Son by the window hears the door, turns to it and takes two steps toward it | MS, push | relaxed bent elbows, arms swing on the steps |
| S05 | 2.2 | "…was kidnapped" | Dark-jacketed man in the open doorway points out; the son walks to the door | wide room | **no grab/no contact** between the two; no distress close-up |
| S06 | 2.0 | "years prior… and all of the calls" | Singer walks along the brick wall to the payphone. **Logo: club poster on the wall** (dark logo, flat-on, ~25% of frame width, ≥1 s) | wide → medium, push | — |
| S07 | 1.4 | "…had to be made from payphones" | The payphone itself, handset on the hook | close push-in | **no hands** (coin-in-slot pinch re-staged out) |
| S08 | 1.4 | "He would…" | Handset at his right ear, eyes darting | MCU front-left | `grip_object` closes the hand on the handset at the first frame; the handset then rides in the hand (Child Of) and the wrist keeps it at the ear; cord is a keyed bezier from the phone |
| S09 | 1.2 | "…terrified" | CU, brows up, small pull-back | CU | same handset method |
| S10 | 1.6 | "…that he would run out of coins" | Two last dimes on the coin ledge; he glances down, handset at his ear | close on the ledge, singer in frame | **no grip**: coins rest on the ledge |
| S11 | 1.6 | "…to negotiate with the kidnappers" | Talking urgently into the handset, free hand hanging | MS | — |
| S12 | 1.4 | "Two days later…" | Singer walks along the suburban pavement | wide | arms swing |
| S13 | 1.8 | "…the son was released" | Son walks from the black car toward his father; father steps, hands lift | wide-medium | — |
| S14 | 1.4 | "…safely" | Father's hands come to rest on the son's shoulders | medium two-shot, side | hands on top of the shoulders (place_hand, 12 mm skin); no hug (arms through backs) |
| S15 | 1.4 | "But he never forgot that fear" | CU, looks down then away | CU, push | — |
| S16 | 1.4 | "…of being helpless" | ECU, slow breath | ECU push-in | — |
| S17 | 1.8 | "So he carried ten dimes exactly with him" | Back at the club years later, he looks down at the ten dimes on his side table, faint smile | MS 3/4 | no grip |
| S18 | 1.6 | "…for the rest of his life" | Years on, singing at the stand mic again, small nod | MS from the left (mic clear of the face) | pocket pat cut (didn't read) |
| S19 | 1.6 | "And when he was buried…" | Cemetery: casket with flowers; his daughter walks up along it toward the camera side | medium-wide from the casket's end | closed casket, no body shown; no logo |
| S20 | 1.4 | "…his daughter…" | MCU, hands folded low, looking down | MCU from past the casket end | camera clear of the lid (no slab in the lens) |
| S21 | 1.8 | "…placed ten dimes in his pocket" | The ten dimes lie on the closed casket lid by the flowers; she stands behind, looking down | close push-in on the dimes | **no hand**: the placing-hand version went wrong twice (arm to her own shoulder, fingers into the lid), re-staged per §2.15; see question 1 |
| S22 | 1.6 | "…for him." | Closing wide: dimes on the lid, flowers, daughter standing | wide push-in | — |

Total ≈ 35.7 s expected (clips 46.4 s).

## Logo
One placement: the club poster on the brick wall in S06 (dark logo on cream paper). Not in the kidnapping or funeral scenes.

## Director answers (round 1)
- Closed casket with the dimes on the lid: OK.
- Dimes on the table/ledge instead of the x-ray: OK.

## Questions for the director (round 1, answered above)
1. **"in his pocket" (S21):** to stay respectful I show a **closed** casket with the ten dimes lying on its lid and the daughter behind; the VO carries "pocket". If you want the pocket literally, the alternative is a tight shot of the jacket pocket in an open casket (no face), coins slid in by her hand. Which do you prefer?
2. The reference shows an x-ray "coins in the pocket" cutaway (S02/S10). Following LESSONS §2.13 (no see-through solids) I replaced it with dimes resting on a table and a coin ledge.
3. The reference's "thought bubble" kidnapper graphic is not used (brief).

## v002 VO layout (frames = 1 + round(word seconds × 60))
| Shot | Frames | VO |
|---|---|---|
| S01 | 1–79 | "Frank Sinatra always carried" |
| S02 | 80–203 | "ten dimes in his pocket," |
| S03 | 204–359 | "and the reason was actually pretty sad." |
| S04 | 360–474 | "Years earlier, his son had been" |
| S05 | 475–607 | "kidnapped, and all the ransom negotiations" |
| S06 | 608–699 | "had to be made through" (logo poster) |
| S07 | 700–751 | "payphones." |
| S09 | 752–829 | "Sinatra was terrified he" |
| S10 | 830–899 | "might run out of coins while" |
| S11 | 900–1007 | "speaking to the kidnappers." |
| S12 | 1008–1063 | "His son was eventually" |
| S13 | 1064–1129 | "released safely" |
| S14 | 1130–1199 | "after two days." |
| S15 | 1200–1284 | "But Sinatra never forgot" |
| S16 | 1285–1392 | "that feeling of helplessness." |
| S18 | 1393–1492 | "So for the rest of his life," |
| S17 | 1493–1597 | "he carried ten dimes everywhere." |
| S19 | 1598–1711 | "And when he was buried," |
| S20 | 1712–1769 | "his daughter placed" |
| S21 | 1770–1868 | "ten dimes in his pocket." |

S08 (phone MCU) and S22 (closing wide) are not used. Every shot is its 1× clip trimmed; none is stretched.
Director Phase-2 note applied: the fedora is tipped back 4° more (S16 eyes clear of the brim).

## v002 preview-round fixes (found by watching the preview)
- S10: camera close on the two dimes on the ledge.
- S14: the father's hands rise beside him and through the gap between them, then rest on the son's shoulders (they no longer pass in front of the son's waist).
- S17: low 3/4 with the ten dimes on the table in the foreground and his face above.
- S19: she walks up and stops at the casket's end, fully in view (no longer hidden behind the casket).
- S20: shot from the casket's other side, so the background is the cemetery, not the neighbouring suburb set.

## v002b (director notes on v002)
- The singer's irises are dark brown (they were pale blue-white and read as glowing), with slightly warm whites and the camera catchlight. Every shot was re-rendered.
- S02 (f80–203): starts above the table, so no body sliver at the frame edge, then a slow push-in onto the dimes.
- Relaxed, bent elbows with a weight shift (hips sway, feet planted) and one small gesture each:
  - S11 (f900–1007): the free hand opens in a pleading gesture mid-shot.
  - S14 (f1130–1199): both men; the father nods with a small palm-up gesture out to his side.
  - S18 (f1393–1492): on stage; his left hand slides into his trouser pocket.
  - S17 (f1493–1597): a small open-hand gesture toward the dimes.

## v002c (director notes on v002b)
- **Dimes:** rebuilt as real coins: 17.9 × 1.35 mm discs with a raised rim (recessed field), flat-shaded faces,
  smooth milled edge, laid flat in two shingled rows of five so all ten can be counted.
  Metal `M_Dime` is (0.30, 0.31, 0.33), roughness 0.28, metallic 1, matching the ledge pair.
  The club-table pile (S02, S17) is seen from above under the club lights, where that still read white, so it uses
  `M_DimeTable` (0.12, 0.124, 0.132), roughness 0.30, metallic 1 (02_sets.py; applied to the built file by `scripts/dime_table_mat.py`).
- **Singer's eyes:** iris saturated dark brown (major 0.09/0.032/0.007, minor 0.040/0.014/0.003, outer 0.022/0.008/0.002)
  because AgX greys out low-saturation browns. Iris-to-white relation 0.50 (larger iris), eye clearcoat 0.05 (the sky
  reflection washed the iris out).
- Re-rendered and spliced preview ranges: 1–371, 608–699, 752–1199, 1200–1597, 1770–1868 (all of the singer's shots plus the dime shots).
