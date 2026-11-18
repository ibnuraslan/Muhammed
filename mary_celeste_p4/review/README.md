# Mary Celeste — Part 4 of 5 (barrels, pump, drift) — storyboard

Script: `mary_celeste/SCRIPT.txt` (branch `claude/mary-celeste`), lines 31–38, word for word, not edited.
From "When the cargo is unloaded in Genoa, nine barrels are empty." to "…sent them over the side." ≈ 2:55 at ~140 wpm.
Look: Atrium (rich warm colour: oxblood, walnut, brass, lamp amber; one cool exterior per location).
16:9, 2560×1440, 24 fps, Cycles. Frames in `review/` are real 3D renders of the shot scenes (low samples).

Sets (all new, in `mary_celeste_p4/`, built on the shared `mary_celeste_3d/lib` ship, sea, Deveau, look, grade):
Genoa quay · cutaway hold (explainer) · hold interior · oak studio (explainer) · deck (day as found / dusk / night / dawn) ·
chart table with a **real 3D relief map** (AWS Terrain Tiles: SRTM + GEBCO bathymetry) · Santa Maria island (real terrain, true scale).
New shared assets: `lib/barrels.py` (40-gal barrels, white/red oak, hold stow), `lib/pump.py` (1870s common pump, intact and dismantled),
`lib/briggs.py` (Captain Briggs, built on the shared Deveau character), `lib/terrain.py`, `lib/cutaway.py`.

| # | ~TC | VO (exact words) | Shot | Action / move | Card / text | SFX |
|---|---|---|---|---|---|---|
| S01 | 0:00 | When the cargo is unloaded in Genoa, | Wide, Genoa quay at late sun: the ship alongside, barrels stowed on the cobbles, ochre and terracotta facades | slow lateral dolly | PLACE left: GENOA, ITALY / 1873 | gulls, harbour lap, hawser creak, cart wheels on cobbles |
| S02 | 0:04 | nine barrels are empty. | Medium high: the nine red-oak barrels set apart, a chalk X on each head | slow push down | — | hollow knock on an empty barrel, chalk scrape |
| S03 | 0:07 | For anyone trying to explain why Briggs might have put his family in a small boat, | MCU Briggs on deck at dusk, looking forward to the boat on the main hatch | slow drift | PERSON right: BENJAMIN BRIGGS / CAPTAIN, MARY CELESTE | wind in rigging, hull creak |
| S05 | 0:13 | those barrels are worth a closer look. If alcohol leaked into the hold, vapor could have collected below deck. | **Cutaway explainer** (port half removed): the hold packed with barrels in tiers; vapour thickens under the deck as the shot runs | slow push + descend, 12 s hold | — | low drone, liquid trickle, creak of the stow |
| S06 | 0:25 | The people above might have feared a fire or an explosion. | ECU the lantern flame hanging in the hold among the barrels, haze | lantern swings with the roll | — | flame flutter, lantern ring creak |
| S07 | 0:29 | An incident like that could give a captain a reason to get everyone away from a ship that otherwise looked capable of sailing. | Wide from the sea: the ship under full sail at dusk | slow track alongside | — | bow wash, sails filling |
| S08 | 0:36 | There are problems with that explanation. | Wide, locked off, low on the water: the ship as found, torn sails, no one at the wheel | locked (sea, sails move) | — | wind, flogging canvas |
| S09 | 0:39 | Deveau's party reports no smell of alcohol fumes. | MCU Deveau leaning over the open fore hatch, breathing in | small breath, eyes half shut | — | a sniff, wind |
| S10 | 0:43 | The main cargo hatch is still secured when they board. | Low insert: main hatch cover with battens and wedges; Deveau soft behind | push in | — | boot on deck, tap on a wedge |
| S11 | 0:47 | The nine empty barrels were described as red oak, a more porous wood than the white oak used for the others. | **Oak explainer** on a lamp-lit table: a white-oak barrel and a red-oak barrel, a stave of each in front | slow push | labels WHITE OAK / RED OAK (Courier Prime) | wood set down on wood |
| S12 | 0:55 | That gives the missing alcohol a possible explanation on its own. | Macro: red-oak end grain, open pores in the earlywood rings, beads of spirit standing out (white oak's pores plugged) | slow rack across | — | faint drip |
| S13 | 0:59 | Nobody can tell from the empty barrels whether they leaked slowly | In the hold: the red-oak barrel in the bottom tier, a dark stain under it | push in | — | drip into bilge |
| S14 | 1:03 | or whether anything happened suddenly enough to make ten people climb over the side. | The hold, along the gap between the stows; the lantern swings | slow dolly forward | — | creak, slosh |
| S15 | 1:07 | (cont.) | The rail gap and empty boat chocks on deck | slow push toward the gap | — | wind through the gap |
| S16 | 1:10 | There's another clue Deveau finds before anyone counts the barrels. | MCU Deveau turning his head aft | head turn (small, ~20°) | — | footstep stops |
| S17 | 1:14 | One of the ship's pumps has been taken apart. | Medium wide low: the port pump open, spear and box on deck, brake unshipped; Deveau looking down at it | slow push | — | iron clank as he nudges the spear |
| S18 | 1:18 | The ship had previously carried coal and had recently been refitted. | The empty hold before loading: coal dust and wood shavings on the ceiling, a shaft of daylight | slow dolly | PLACE left: NEW YORK / OCTOBER 1872 | distant hammers, saw |
| S19 | 1:23 | More than a century later, documentary researcher Anne MacGregor looks at those two facts alongside the dismantled pump. | The investigation table (lamp, papers, slate, relief map) — no figure: living researchers are not depicted | slow drift | PERSON right: ANNE MACGREGOR / DOCUMENTARY RESEARCHER (text card; no free photo) | paper turned, lamp hiss |
| S20 | 1:30 | Coal dust or debris from the work could have fouled it. | **X-ray macro** of the pump's upper box: the leather flap valve held open by coal grit and a shaving | slow orbit | — | grit crunch, valve slap |
| S21 | 1:34 | A pump in pieces suggests someone may have been trying to find out why it wouldn't work. | Night, lantern: Briggs drawing the spear up out of the pump | pull (arms) | — | iron rod scraping in the bore, rain |
| S22 | 1:40 | The record can't tell us what they found. | Top-down: the parts on deck by daylight, as found | locked (rope end stirs) | — | wind, silence of the deck |
| S23 | 1:43 | MacGregor and oceanographer Phil Richardson also go back to the slate. | Insert: the log slate on the table, the last entry in chalk ("At 8 Eastern point bore SSW 6 miles distant.") | slow push | PERSON right: PHIL RICHARDSON / OCEANOGRAPHER (text card) | chalk tap |
| S24 | 1:48 | They have two points to work with. | High wide: the real 3D relief map of the Azores and the ocean east | slow push | — | map paper rustle |
| S25 | 1:51 | The last recorded sighting of Santa Maria, | Close: Santa Maria in relief; brass pin; soft filled orange band spreads from it | push | label 25 NOV 1872 · 8 A.M. | pin tap, soft pulse |
| S26 | 1:54 | and the place Deveau's ship found the Mary Celeste. | Close: second pin 400 miles east; orange band | drift | label 38°20′N 17°15′W | pin tap, pulse |
| S27 | 1:58 | Using historical weather data, they test whether a ship with nobody steering could get from one to the other. | The map: wind strokes across it, the drift path inks itself pin to pin, a model brigantine travels on it | path draws over 6 s | — | pen nib scratch, wind |
| S28 | 2:05 | It could. | The model arrives at the second pin (hold) | locked | — | soft stop click |
| S29 | 2:07 | That matters because it puts a possible evacuation within sight of land. | Wide at dawn from the sea: the ship, Santa Maria grey-blue on the horizon (real terrain, ~11 km) | slow drift | — | sea, gulls far off |
| S30 | 2:12 | After a stretch of rough weather, | Night, heavy sea: the ship labouring, lantern on the quarterdeck | camera heaves with the sea | — | storm wind, wave slam |
| S31 | 2:15 | Briggs may have been trying to judge how much water was coming in and whether the pumps could keep up. | Night MCU: Briggs draws up the sounding rod, reads the wet mark by the lantern | rod up, eyes down | — | line through hands, drip |
| S32 | 2:21 | With the hold packed full of barrels, he couldn't simply look down and see what was happening at the bottom. | **Cutaway callback**: camera sinks from the deck through the tiers to the dark bilge water | descend 6 s | — | muffled slosh |
| S33 | 2:28 | If he believed the water was winning, Santa Maria would have been the one place he could see that offered a way off the ship. | Dawn: Briggs at the rail, the island beyond (OTS → MCU push) | slow push to the eyes | — | wind, a breath |
| S34 | 2:36 | That's one possible reading of the evidence. | The table: two pins, the inked drift, the lamp | slow pull back | — | lamp hiss |
| S35 | 2:40 | The water Deveau measures is what's there when he boards. | Day MCU: Deveau reads the sounding rod | small tilt of the rod | label 3½ FEET | drip, line |
| S36 | 2:45 | We don't have the reading Briggs was working with, or even know that water was the danger that sent them over the side. | Wide: the empty ship sails on; slow pull back | pull back | — | sea, wind fades |

Rules applied: no flat 2D (map = relief mesh on a table, island = true-scale terrain); hands only with their person in frame;
no living person depicted (MacGregor, Richardson as text cards over their work); bands are filled soft orange; cards slide (person right, place left, shared callout.py);
Courier Prime captions; every action has an SFX (list above → `sfx_cues.csv` at render time).

## Frames
`S01.jpg` … `S36.jpg` (no S04): one real Cycles render per shot from `shots/board.py`, 1024×576, 40 spp + OIDN, taken at mid-shot (t = 0.5).
`CONTACT_SHEET.jpg`: all of them. Ungraded house finish; cards and captions are not burned in yet.

## Known issues to fix before the final
* S05 cutaway: the alcohol vapour volume does not read yet (will be a visible warm haze thickening under the deck).
* S13 hold: too dark; the stain under the red-oak barrel must read.
* Deveau/Briggs faces: dark strands near the temple/cheek at this resolution (shared Deveau hair growth); to check at full res.
* S31/S35 rod-reading pose: hands are on the rod but the grip reads stiff; will refine.
* Cards (Genoa, Briggs, Santa Maria, New York) need free-licence photos: this container cannot reach Wikimedia/LOC.

## Render budget (measured here: 4 CPU cores, no GPU)
~15 s/frame at 640×360/24 spp → full spec 2560×1440 at ~96 spp ≈ 15–20 min/frame. 175 s × 24 fps = 4,200 frames
≈ 1,000+ machine-hours on one container: not feasible as is. Options for the hub:
A) render 1280×720 at 48 spp + OIDN, upscale to 2560×1440 (≈ 2 min/frame ≈ 140 h on one box; ≈ 18 h split over 8 sessions);
B) A at 12 fps + motion-interpolation to 24 (halves it; risks artefacts on people);
C) full 2560×1440 only if the render is split across many sessions/GPUs.
