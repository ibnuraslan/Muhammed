# B05 LoveCanal v002b: The Love Canal Disaster (built to the client VO)

Vertical explainer, 1080×1920, 60 fps, 32.75 s (frames 1–1966), Cycles. 20 shots with hard cuts on one camera, timed to the client's VO (`LoveCanal_v002b_VO.mp3`, transcribed with faster-whisper; `beats.json` lists every shot's start frame and first words).

## Files
- `LoveCanal_v002b_60fps.blend`: the RenderStreet package (see SETTINGS.md)
- `LoveCanal_v002b_VO.mp3`: the client VO
- `beats.json`: shot start/end frames at `1 + round(seconds × 60)` of the VO words
- `review/preview.mp4`: moving preview of the exact package (every 5th frame, 270×480, Cycles 4 spp + OIDN, with the VO)
- `review/pages/`: contact pages of every preview frame
- `review/*_check.json`, `review/clip_scan.json`, `review/body_prop_cross.json`: check outputs
- `scripts/`: the full build (01 chars → 02 sets → 03 animation/camera → anim_look → 04_shrink → package_for_farm)

## Shot list (VO words)
S1 neighbourhood, boy on bike ("People living in this neighborhood") · S2 neighbour at the fence smells it ("started noticing strange smells") · S3 neighbour lifts the trash lid ("during the 1970s") · S4 father tastes the water ("Their water tasted odd") · S5 kitchen, father sick, family watching ("and residents began getting sick") · S6 house, neighbour walks by ("But what they didn't know") · S7 ground cut-away under the homes ("was that their entire neighborhood had been built") · S8 the toxic pocket ("on top of a toxic waste dump") · S9 worker rolls a drum ("Decades earlier") · S10 dump trucks, worker waves ("a chemical company had") · S11 trucks tip, drums slide off ("buried more than 20,000") · S13 the drum heap ("tons of hazardous chemicals") · S14 bulldozer buries it ("there") · S15 house frames rise on the cut-away ("Once houses were built above it") · S16 basement seep ("the chemicals began leaking into basements") · S17 backyard puddle ("backyards") · S18 water tower ("and the water supply") · S19 box to the moving truck, logo ("Eventually") · S20 truck leaves ("families were evacuated") · S22 hospital, father and son ("and many residents suffered long-term health problems").

The VO is 10 s shorter than the reference. S12 (top-down pile) and S21 (wide street) are folded into their neighbours, and S4's action was re-keyed at 1× to fit its 1.7 s (nothing time-stretched).

## v002b (director notes on v002)
- The father (teal shirt) has his own short dark hair. He is not the trash-can man (Dad2, blue shirt), so the hair is not matched to his.
- S4 (325–427) reframed waist-up (no crotch line). The father's trousers are looser (pushed out along their normals, more toward the hem).
- The neighbour/mother (S1–S2, S6) wears a mid-blue dress with small cream dots and a looser skirt instead of the cream one.
- S5 (428–563) pushes in. The boy looks down, lifts his head to his parents, then takes two small steps toward them along the end of the island.
- S22 (1785–1965): a closer, higher camera with a slow push. The boy stands at the bedside, and father and son hold hands palm to palm above his chest, in view the whole shot. The hospital walls and floor are deeper and the overhead fill is lower, with a warm key from the window side.

## Checks on the package (review/)
The full-film checks ran on the package before the last S22 lens change (38→44 mm, camera only). S22 (1785–1966) was re-checked on the final package (`review/*_S22_recheck.json`): qa 0 flags, clip_scan 0 bad ranges, limb_check only the known shoulder false positive.
- body_prop_cross:
  - The accepted contacts: S1 riding (1–76), S4 thumb on the glass (349–394), S9 fingertips on the drum (952–973), S19 fingertips on the box (1609–1693).
  - S22 1785–1966: the father's feet and pelvis meet the draped blanket, and a thigh meets the bed frame below the mattress. All of these are under the blanket or the mattress and outside the tight frame. Nothing pokes through on screen.
- limb_check ARMBODY: upperarm01 points within 4 cm of the shoulder (known false positive), except S4 349–385, where the right forearm is tucked to his side while he sips (hand and glass read clearly).
- clip_scan, explained ranges:
  - 79–199 (S2 neighbour/mother) and 259–319 (S3 trash-can man): relaxed hanging fingertips touch the side of the thigh; those hands are hidden behind the body and the bin.
  - 433–613 (S5): the same for the mother behind the island. The father's hand is at his mouth (493–499).
  - The v002 S22 range is gone.
- qa_check: EMPTY on the set/prop shots (S7, S8, S11–S18), CAMJUMP at the 19 hard cuts, and PROPMOVE for intended unaided motion: drums off the tipping beds (S11/S13), seep streaks (S16), the yard puddle (S17), tower drips (S18), and the glass on the counter at the S4→S5 cut. BACKHEAD on single frames 1 and 565.

## Known issues
- S4 397–410: the left arm swings out briefly as the hand lifts to the chest.
- S10 975–1033: the two trucks sit partly at the frame edges.
- S17 1495–1510: the puddle starts tiny (it grows on the beat).
