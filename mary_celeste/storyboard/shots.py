"""Shot list: The Ship That Came Back Without Its Crew.

Each shot: s = sentence index (or (a, b) inclusive range, or None for a no-VO beat).
Consecutive shots with the same s share that VO span; w = relative weight.
dur is used only for no-VO beats (silences, pre-roll, tail).
"""

SHOTS = []

DEV = "Oliver Deveau"
MOR = "Capt. David Morehouse"
BRI = "Capt. Benjamin Briggs"
SAR = "Sarah Briggs"


def sh(s, size, mv, camera, action, light, sfx, sk, w=1.0, dur=None, card=None, tag=None, note=None,
       silence=False, part=None, blur=0):
    if blur:
        sk = dict(sk, blur=blur)
    SHOTS.append(dict(s=s, size=size, mv=mv, camera=camera, action=action, light=light, sfx=sfx, sk=sk, w=w,
                      dur=dur, card=card, tag=tag, note=note, silence=silence, part=part))


# ---------- sketch shorthands ----------
def MC(x=0.5, L=0.3, sails="torn", face=1, y=None, **k):
    d = dict(x=x, L=L, sails=sails, face=face, **k)
    if y is not None:
        d["y"] = y
    return d


def DG(x=0.5, L=0.3, sails="full", face=1, y=None, **k):
    return MC(x, L, sails, face, y, tone=30, **k)


def SEA(mood="noon", **k):
    return dict(scene="sea", mood=mood, **k)


def DECK(mood="noon", cam=None, **k):
    return dict(scene="deck", mood=mood, cam=cam or dict(hz=0.40, camH=1.5), **k)


def CAB(mood="cold", cam=None, **k):
    return dict(scene="cabin", mood=mood, cam=cam or dict(hz=0.45, camH=1.45), **k)


def INS(prop, mood="cold", **k):
    return dict(scene="insert", prop=prop, mood=mood, **k)


def FACE(mood="noon", **k):
    return dict(scene="face", mood=mood, **k)


def P(X, Z, view="3q_l", **k):
    return dict(X=X, Z=Z, view=view, **k)


CAP = dict(hat="cap")
SKY_NOON = dict(sky=(215, 170), sea=(135, 60))
SKY_DAWN = dict(sky=(235, 190), sea=(150, 70))
SKY_STORM = dict(sky=(120, 80), sea=(80, 25))

# ======================================================================
# COLD OPEN — 4 Dec 1872, aboard the Mary Celeste
# ======================================================================
sh(None, "EWS · 24mm · wave height", "push", "Slow push-in at wave height toward the lone ship; swell lifts the lens",
   "No people. The Mary Celeste alone on grey swell, sails torn, heeling and making way under the wind",
   "Overcast winter noon, flat silver sky, haze on the horizon",
   "Wind bed, wave slap on the lens housing, distant canvas flog, rigging creak", SEA(ships=[MC(0.5, 0.33)], **SKY_NOON),
   dur=4.0, silence=True, note="Pre-roll: 4 s of pure ambience before the first word.")
sh(0, "MS · 35mm · low", "crane_u", "Hero one-take (8 s): crane up the hull with Deveau as he climbs, ending over the rail",
   "Deveau climbs from the Dei Gratia boat up the Mary Celeste's chain-plates; two rowers hold the boat off with oars",
   "Overcast; cold soft top light, wet hull glints",
   "Boat thuds hull, oar knocks, water slap, boots on chain-plate, his breath", dict(scene="hull", mood="noon"), w=1.4)
sh(0, "MCU · 85mm", "push_slow", "Slow push to his eyes as his head clears the rail",
   "Deveau's face rises over the rail, eyes scan the empty deck; small frown",
   "Overcast top light, half face in shadow",
   "Wind through rigging, a loose block knocking", FACE(bg="sea", hat="cap", beard=True, expr="worry"),
   card=("r", "OLIVER DEVEAU", "First mate, Dei Gratia"))
sh(1, "WS · 28mm · deck height", "track_r", "Track behind him (2 s back view) as he walks forward",
   "Deveau walks forward along the deck (back view, short), passing an open hatch; the main boom swings with the roll",
   "Overcast; deck wet and reflective",
   "Boot steps on wet planks, boom creak, canvas flog", DECK(hatches=[(1.4, 7, 8.5, True)], masts=(9, 17),
   people=[P(0.4, 5.0, "back", **CAP)]))
sh(1, "MS · 35mm", "tilt_d", "Tilt down with him as he goes down the companionway",
   "Deveau turns into the after companionway and climbs down the ladder, one hand on the rail",
   "Daylight above, darkness below",
   "Ladder creak, wind drops away as he descends", DECK(cam=dict(hz=0.30, camH=1.8), hatches=[(0, 3, 4.5, True)], masts=(12,),
   people=[P(0.2, 4.0, "3q_r", pose="bend", **CAP)]))
sh(2, "WS · 24mm · cabin", "static", "Locked-off wide; he enters frame through the doorway and stops",
   "Deveau stops inside the captain's cabin; water on the floor; skylight open above the bunk",
   "Cold daylight shaft through the open skylight; rest of cabin dark",
   "Drips, hull creak, sea muffled through planking", CAB(water=True, people=[P(0.7, 3.2, "3q_l", **CAP)]))
sh(2, "OTS insert · 50mm", "push", "Over his shoulder: push in as he presses the blanket",
   "Deveau (head and shoulder in frame) presses the bedding; water wells up around his fingers",
   "Skylight shaft rakes across the wet cloth",
   "Squelch, slow drips", INS("blanket", arm_to=(0.5, 0.58), hat="cap", px=0.55, py=0.62, ps=0.2))
sh(3, "HIGH · 35mm", "push_slow", "High angle, very slow push-in on the bunk",
   "A small, shallow hollow in the wet mattress, child-sized; Deveau's shoulder at the frame edge",
   "Single cold shaft; hollow catches a soft shadow",
   "Room tone thins; one drip", CAB(cam=dict(hz=0.18, camH=2.6), hollow=True, table=False, skylight=True), w=1.4)
sh(3, "CU · 85mm", "static", "Locked-off; only his eyes move",
   "Deveau's reaction: brows tighten, breath held",
   "Skylight light from above, eyes in shadow then catching light",
   "Hull groan", FACE(mood="cold", bg="cabin", hat="cap", beard=True, expr="worry", s=0.5, light="c"))
sh(4, "MS · 50mm", "pan_r", "Pan with him",
   "Deveau pulls back the bunk curtain and checks the narrow space beside it: empty",
   "Cold; deep shadow behind the curtain",
   "Curtain rings scrape on the rod", CAB(people=[P(-0.7, 2.6, "left", pose="bend", **CAP)], skylight=True))
sh(None, "WS · 24mm", "static", "Locked-off (2 s), nothing but the creak",
   "Deveau stands still in the centre of the cabin, alone in the shaft of light",
   "Cold shaft only", "SILENCE before the reveal: music out, only one creak",
   CAB(people=[P(0.0, 3.0, "front", **CAP)]), dur=2.0, silence=True)
sh(5, "TOP-DOWN · 24mm", "crane_u", "Crane straight up out through the skylight",
   "Deveau small and alone below; camera exits through the open skylight to the empty deck",
   "Cold shaft, then grey daylight as we exit",
   "Wind returns as we clear the skylight", CAB(cam=dict(hz=-0.2, camH=4.0), people=[P(0.0, 2.2, "back", **CAP)], table=True))
sh(6, "WS · 28mm · low on deck", "track_l", "Low lateral track along the bulwark",
   "Deveau steps out of the companionway and turns; a section of the bulwark rail has been taken out and laid flat on the deck",
   "Overcast; rail edge catches the sky",
   "Boot steps, wind, canvas flog", DECK(cam=dict(hz=0.38, camH=0.9), gap=(-1, 3.0, 5.0), rail_flat=(-1, 2.6, 5.2),
   people=[P(1.2, 6.5, "3q_l", **CAP)]))
sh(6, "OTS insert · 50mm", "push", "Over his shoulder as he crouches",
   "Deveau (head + shoulder in frame) runs his hand along the removed rail lying flat; bare bolt holes",
   "Flat daylight; wet wood",
   "Hand on wet wood, faint scrape", INS("rail", bg="deck", arm_to=(0.48, 0.55), hat="cap", py=0.6, ps=0.22, mood="noon"))
sh(7, "LOW POV · 24mm", "push", "Push slowly through the gap toward open sea",
   "Through the gap in the bulwark: open sea; wave crests pass below the opening",
   "Overcast; sea darker than sky",
   "Wave wash suddenly loud through the gap", SEA(fg="gap", **SKY_NOON))
sh(None, "TOP-DOWN · 35mm", "static", "Locked-off top-down (2 s)",
   "The boat chocks on the main hatch are empty; cut lashing ends lie on the deck; Deveau's boots at frame edge",
   "Flat overcast", "SILENCE before the reveal: wind only",
   INS("chocks", bg="deck", side=None, py=0.5, ps=0.18, mood="noon"), dur=2.0, silence=True)
sh(8, "CU · 85mm", "push_slow", "Very slow push",
   "Deveau looks out to sea through the gap; wind moves his hair and collar",
   "Overcast, soft side light",
   "One long gust; no music", FACE(bg="sea", hat="cap", beard=True, view="left", light="l"))
sh(9, "WS · 35mm", "track_r", "From the gap: track with the boat",
   "Deveau and the rowers pull back across the swell toward the Dei Gratia (seen through the gap)",
   "Overcast; Dei Gratia grey in the haze",
   "Oars, oarlocks, water", SEA(fg="gap", boats=[dict(x=0.5, y=0.66, L=0.10, people=3)], ships=[DG(0.5, 0.18, y=0.52)], hy=0.52))
sh(10, "MS · 35mm", "handheld", "Handheld at deck level among the men",
   "Deveau and two sailors haul a halyard together hand over hand; a sail climbs the mast",
   "Overcast, wind on faces",
   "Rope through block, grunts, canvas fills with a boom", DECK(cam=dict(hz=0.55, camH=1.2), masts=(5,),
   people=[P(-0.8, 3.2, "3q_r", arms=[(-1, 0.05, -0.32), (1, 0.08, -0.36)], **CAP), P(0.1, 3.6, "3q_r", arms=[(-1, 0.05, -0.32), (1, 0.08, -0.36)], **CAP),
           P(0.9, 4.2, "3q_l", arms=[(-1, -0.05, -0.30), (1, -0.02, -0.36)], **CAP)]))
sh(10, "EWS · 24mm · high", "crane_u", "Crane high as she bears away",
   "The Mary Celeste under reduced sail turns away; the Dei Gratia small in the distance",
   "Overcast; a thin break of light on the sea", "Wind swell; first music cue",
   SEA(ships=[MC(0.4, 0.3, sails="spare"), DG(0.82, 0.08)], hy=0.4))
sh(11, "MS · 35mm · hip height", "track_r", "Slow lateral track through the forecastle",
   "Empty crew bunks and sea chests left behind, clothes still inside; nobody",
   "Dim; daylight leaking through the fore hatch",
   "Slosh, timber creak, a chest lid rattles with the roll", CAB(cam=dict(hz=0.5, camH=1.0), bunk=True, chest=True, table=False, skylight=False, port=True))
sh(12, "WS · 24mm · water level", "push_slow", "Low at the waterline, slow push toward the stern",
   "Hull ploughs through swell, intact; carved name MARY CELESTE on the stern board",
   "Overcast; spray backlit",
   "Hull swish, wave crash, music lifts", SEA(ships=[MC(0.5, 0.6, y=0.62)], hy=0.55))
sh(None, "WS · 24mm", "static", "Hold the wide (2 s)", "She sails on, empty",
   "Overcast", "Ambience only, music tail", SEA(ships=[MC(0.55, 0.25)]), dur=2.0)

# ======================================================================
# 4 DECEMBER 1872 — DEI GRATIA
# ======================================================================
sh(13, "EWS · 24mm · wave height", "track_r", "Low tracking alongside, skimming waves",
   "The Dei Gratia under full sail crossing the Atlantic; two men work aloft",
   "Overcast noon, cold silver light",
   "Bow wash, wind, rigging, sails drawing", SEA(ships=[DG(0.5, 0.42, y=0.58)], hy=0.56),
   w=1.2, tag="DECEMBER 4, 1872 · NORTH ATLANTIC", card=("l", "DEI GRATIA", "Brigantine, cargo"))
sh(13, "MS · 50mm", "push_slow", "Slow push",
   "Below, Deveau at the mate's table, working on papers by the port light",
   "Port daylight + dim interior",
   "Creak, pen scratch, muffled sea", CAB(mood="cold", people=[P(0.3, 2.6, "3q_l", pose="sit", **CAP)], skylight=False, port=True, bunk=True))
sh(14, "MCU · 50mm", "static", "Locked; he leans into frame",
   "The helmsman at the wheel, both hands on the spokes, squints and leans forward",
   "Overcast, eyes shaded by cap",
   "Wheel spokes creak, wind", FACE(bg="sea", hat="cap", view="3q_r", light="r", expr="frown"))
sh(14, "POV · 200mm", "push", "Long-lens POV, slow push into haze",
   "Tiny sails on the horizon",
   "Haze, low contrast", "Wind; a single low pulse", SEA(ships=[MC(0.62, 0.05)], hy=0.5, fog=1))
sh(14, "MS · 35mm", "static", "Locked", "Helmsman lifts one arm and points (whole body in frame)",
   "Overcast", "Wind, the helmsman's shout carried away (no lip-sync, seen from behind)",
   SEA(fg="rail", people=[dict(x=0.4, y=1.02, h=0.65, view="back", hat="cap", arms=[(-1, -0.03, 0.34), (1, 0.35, -0.30)])], ships=[MC(0.78, 0.04)]))
sh(15, "MS · 35mm", "tilt_d", "Tilt down to the companionway",
   "Morehouse leans over the companionway and calls below",
   "Overcast top light",
   "Call muffled below decks, wind", DECK(cam=dict(hz=0.34, camH=1.7), hatches=[(0, 3, 4.5, True)], masts=(12,),
   people=[P(-0.6, 3.6, "3q_r", pose="bend", **CAP)]), card=("r", "DAVID MOREHOUSE", "Captain, Dei Gratia"))
sh(15, "LOW · 24mm", "crane_u", "From below: Deveau climbs toward the light",
   "Deveau climbs the ladder into daylight, squinting",
   "Hard daylight from above, dark below",
   "Ladder creak, wind rises as he emerges", dict(scene="face", mood="noon", bg="dark", hat="cap", beard=True, view="front", light="c", cy=0.5))
sh(16, "2-SHOT · 35mm", "static", "Locked two-shot",
   "Morehouse lowers his telescope and points; the helmsman spins the wheel",
   "Overcast", "Wheel spins, rudder chains clank",
   SEA(fg="rail", people=[dict(x=0.3, y=1.0, h=0.6, view="3q_r", hat="cap", arms=[(-1, 0.0, 0.3), (1, 0.4, -0.25)]),
                          dict(x=0.68, y=1.0, h=0.6, view="3q_l", hat="cap", arms=[(-1, -0.15, 0.1), (1, 0.12, 0.1)])]))
sh(16, "WS · 24mm · high", "crane_d", "High wide, crane down",
   "The Dei Gratia's wake curves; men haul the braces and the yards swing round",
   "Overcast", "Braces creak, sails thunder then fill", SEA(ships=[DG(0.5, 0.34, face=-1)], hy=0.35))
sh(17, "OTS · 50mm", "push_slow", "Over Morehouse's shoulder, slow push",
   "The Mary Celeste closer, a few hundred metres off, sails ragged",
   "Overcast; she is darker against the haze", "Wind", dict(scene="sea", mood="noon", ships=[MC(0.6, 0.22)], fg="rail"))
sh(17, "MS · 50mm", "static", "Locked, back three-quarter",
   "Two sailors at the rail cup their hands and call across (no lip-sync, faces turned away)",
   "Overcast", "Shouts carried off by the wind",
   SEA(fg="rail", ships=[MC(0.72, 0.12)], people=[dict(x=0.3, y=1.02, h=0.62, view="back", hat="cap", arms=[(-1, 0.1, -0.2), (1, 0.15, -0.2)]),
                                                 dict(x=0.5, y=1.04, h=0.6, view="back", hat="cap", arms=[(-1, 0.1, -0.2), (1, 0.15, -0.2)])]))
sh(None, "WS · 85mm", "static", "Locked (2 s)", "Mary Celeste's deck seen across the water: nobody at the helm",
   "Overcast", "SILENCE before the line: only canvas flog", SEA(ships=[MC(0.5, 0.45, y=0.6)], hy=0.55), dur=2.0, silence=True)
sh(18, "WS · 85mm", "push_slow", "Continue: slow push on the unmanned wheel", "The wheel stands still; nobody comes to the rail",
   "Overcast", "Wind only", SEA(ships=[MC(0.5, 0.5, y=0.62)], hy=0.55))
sh(19, "LOW · 24mm", "tilt_u", "Tilt up the foremast",
   "Upper topsail full and bellied, drawing wind",
   "Bright sky behind the canvas, sail glows", "Canvas boom as it fills",
   SEA(ships=[MC(0.5, 0.75, y=1.25, sails="torn")], hy=0.95, clouds=True))
sh(20, "CU · 85mm", "handheld", "Long-lens handheld",
   "A torn sail strip whips in the wind; a loose sheet rope swings (moved only by the wind)",
   "Overcast, backlit canvas", "Canvas crack, rope whip",
   SEA(ships=[MC(0.3, 1.2, y=1.6)], hy=1.0, clouds=False))
sh(21, "2-SHOT · 50mm", "static", "Locked",
   "Morehouse lowers his glass and gives Deveau a nod; Deveau nods back",
   "Overcast", "Wind",
   FACE(bg="sea", hat="cap", beard=True, cx=0.62, s=0.36, view="3q_l", second=dict(cx=0.3, cy=0.45, s=0.34, view="3q_r", hat="cap", beard=True, tone=35)))
sh(21, "WS · 35mm", "crane_d", "Crane down with the boat",
   "Men on the falls lower the Dei Gratia's boat; Deveau and two others sit in it",
   "Overcast", "Blocks squeal, rope runs, splash",
   SEA(boats=[dict(x=0.5, y=0.75, L=0.25, people=3)], fg="rail", hy=0.45))

# ======================================================================
# THE DECK
# ======================================================================
sh(22, "MS · 35mm", "push", "Push in on the binnacle",
   "Deveau at the Mary Celeste's helm; the binnacle knocked out of its place; he lifts the hood",
   "Overcast", "Grit of broken glass, creak",
   DECK(helm=(0.6, 3.2), people=[P(-0.4, 3.0, "3q_r", pose="bend", **CAP)], masts=(10,)))
sh(22, "OTS insert · 50mm", "push", "Over his shoulder",
   "Compass glass cracked, card loose; Deveau (head and shoulder in frame) tips it toward the light",
   "Overcast top light", "Glass shards tinkle",
   INS("compass", bg="deck", arm_to=(0.42, 0.62), hat="cap", mood="noon", ps=0.2))
sh(23, "TOP-DOWN · 24mm", "orbit", "Top-down, slow rotate",
   "Two open hatches, covers lying beside them; Deveau and the second mate walk between (top-down hides feet)",
   "Overcast", "Steps, wind, hatch covers knocking",
   DECK(cam=dict(hz=-0.4, camH=12), hatches=[(-1.2, 8, 10, True), (1.2, 13, 15, True)], sea=False, masts=(), people=[]))
sh(24, "LOW WS · 24mm", "static", "Low in the doorway, locked",
   "Galley doorway; water sloshes inside up to the raised lip; Deveau ducks in",
   "Grey light from the door; dark galley",
   "Slosh, drip, door knocks on its hook", dict(scene="galley", mood="cold", people=[P(0.2, 2.0, "back", pose="bend", **CAP)]))
sh(24, "CU · 85mm", "rack", "Rack focus from the lip to the water",
   "Water laps over the raised lip of the doorway as the ship rolls; Deveau's boots beyond",
   "Grey light", "Lapping water", dict(scene="galley", mood="cold", stove_off=False, people=[]), blur=0)
sh(25, "MS · 35mm", "pan_r", "Pan to the stove",
   "The stove shifted off its fittings, stovepipe parted; Deveau puts his palm on the cold iron (body in frame)",
   "Grey door light", "Iron clanks as the ship rolls",
   dict(scene="galley", mood="cold", water=True, people=[P(-0.6, 1.9, "3q_r", **CAP)]))
sh(26, "MS · 35mm", "tilt_d", "Tilt down with the line",
   "Deveau at the pump well feeds the sounding rod down on its line",
   "Overcast", "Line through his hands, rod knocks on the way down",
   DECK(cam=dict(hz=0.45, camH=1.2), masts=(4,), people=[P(0.3, 2.6, "3q_l", pose="bend", **CAP)]))
sh(26, "X-RAY · maquette", "push", "Push in on a white-maquette cutaway",
   "Cutaway of the ship: the rod drops through the pump well into the dark water in the bottom",
   "Neutral white studio light on the maquette", "Deep hull resonance, rod splash",
   dict(scene="xray", mood="maq", water=0.25, rod=True), w=1.2)
sh(None, "OTS insert · 50mm", "static", "Locked (2 s)",
   "Deveau draws the rod up; the wet mark darkens the wood",
   "Overcast", "SILENCE: drip from the rod only",
   INS("rod", bg="deck", arm_to=(0.35, 0.55), hat="cap", mood="noon", ps=0.18), dur=2.0, silence=True)
sh(27, "ECU · 100mm macro", "static", "Locked macro",
   "Thumb on the notch: the wet line on the rod at three and a half feet (cut notches, real marks)",
   "Overcast", "One drip",
   INS("rod", bg="deck", arm_to=(0.48, 0.52), hat="cap", mood="noon", ps=0.3))
sh(28, "WATERLINE · 24mm", "track_l", "Track along the waterline, half underwater",
   "Hull planking and sheathing intact below the waterline",
   "Light through the surface", "Muffled wash, bubbles",
   dict(scene="under", mood="under", diver=False))
sh(29, "LOW · 24mm", "tilt_u", "Tilt up the mainmast from its foot",
   "Deveau at the mast foot looks up the standing mast",
   "Overcast, bright sky", "Rigging hum",
   DECK(cam=dict(hz=0.75, camH=0.5), masts=(3,), people=[P(0.6, 2.8, "3q_l", **CAP)]))
sh(30, "WS · 35mm", "track_r", "Track alongside", "She keeps moving under the sail that's left",
   "Overcast", "Wash along the hull",
   SEA(ships=[MC(0.45, 0.4, y=0.6)], hy=0.55))
sh(31, "MCU · 85mm", "push_slow", "Slow push (decision beat)",
   "Deveau looks from the pump to the Dei Gratia and back; jaw sets",
   "Overcast; soft side light", "Sound pulls back to wind; one pump creak",
   FACE(bg="sea", hat="cap", beard=True, expr="frown", view="3q_r", light="r"), w=1.2)
sh(31, "EWS · 24mm · crane", "crane_u", "Crane high", "Three small figures on a long, empty deck",
   "Overcast", "Wind",
   DECK(cam=dict(hz=0.10, camH=9), masts=(10, 20), people=[P(-0.5, 8, "back", **CAP), P(0.5, 9, "back", **CAP), P(1.5, 10, "back", **CAP)]))

# ======================================================================
# LOGBOOK AND SLATE
# ======================================================================
sh(32, "MS · 35mm", "static", "Locked",
   "Deveau ducks through the low door of the mate's cabin",
   "Small port light; dark", "Door creak, ship creak",
   CAB(people=[P(0.6, 2.6, "3q_l", pose="bend", **CAP)], port=True, skylight=False, logbook=True), w=1.2)
sh(33, "OTS insert · 50mm", "push", "Over his shoulder",
   "Deveau (head and shoulder in frame) opens the logbook on the cabin table",
   "Port light across the page", "Damp page turns",
   INS("logbook", arm_to=(0.4, 0.58), hat="cap", ps=0.22))
sh(34, "WS · 35mm", "pan_r", "Pan from the book to the table",
   "The slate lies on the cabin table; Deveau turns to it",
   "Port light", "Creak",
   CAB(slate=True, people=[P(-0.6, 3.0, "3q_r", **CAP)], port=True, skylight=False))
sh(34, "OTS insert · 50mm", "push", "Over his shoulder",
   "Deveau lifts the slate toward the port light; chalk lines catch the light",
   "Port light raking across the slate", "Slate scrape on wood",
   INS("slate", arm_to=(0.42, 0.62), hat="cap", ps=0.22))
sh(35, "ECU · macro", "rack", "Rack focus along the entries",
   "The last written page; entries stop under the 24th (real ink, real hand)",
   "Port light", "Page flutter", INS("logbook", side="l", arm_to=(0.22, 0.85), hat="cap", ps=0.35))
sh(36, "ECU · macro", "push_slow", "Slow push across the chalk",
   "Chalk entries run on into the next morning; Deveau's cheek soft in the foreground",
   "Raking light", "Soft slate ambience",
   INS("slate", side="r", arm_to=(0.8, 0.85), hat="cap", ps=0.33))
sh(37, "MAQUETTE · 50mm", "push", "Match-cut from the slate into a physical sea-relief maquette",
   "Brass pin at Santa Maria; a soft filled orange band pulses around it",
   "Single warm work lamp over the maquette", "Low pulse, distant sea",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56)], ripple=(0.2, 0.56)), w=1.3,
   card=("l", "SANTA MARIA", "Island, the Azores"))
sh(38, "MAQUETTE · 50mm", "track_r", "Track east across the model sea to a second pin",
   "Second pin far to the east: where the Dei Gratia found her",
   "Warm work lamp", "Low wind whoosh",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.50)], ripple=(0.55, 0.50)))
sh(39, "MCU · 50mm", "push_slow", "Slow push",
   "Deveau holds the slate and looks out of the port at empty sea",
   "Port light on half his face", "Creak; low drone",
   FACE(mood="cold", bg="cabin", hat="cap", beard=True, view="left", light="l", expr="worry"))
sh(39, "MAQUETTE · top", "static", "Locked top-down (hold 3 s)",
   "Nothing between the two pins: the blank stretch of sea",
   "Work lamp", "Drone fades out",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.50)]))

# ======================================================================
# NEW YORK — November 1872
# ======================================================================
sh(40, "EWS · 24mm", "crane_d", "Wipe through a hull timber into New York; crane down to the pier",
   "East River pier: the Mary Celeste moored; carts, stevedores, warehouses",
   "Autumn morning, soft warm haze", "Gulls, cart wheels on cobbles, stevedores' calls, harbour bell",
   dict(scene="pier", mood="nyday", people=[dict(x=0.62, y=0.86, h=0.28, view="3q_l", hat="cap"), dict(x=0.85, y=0.95, h=0.33, view="back", hat="cap")]),
   w=1.3, tag="NOVEMBER 1872 · NEW YORK", card=("l", "NEW YORK", "East River, Pier 50"))
sh(40, "WS · 35mm", "crane_d", "Crane down the rigging to the deck",
   "A barrel swings aboard in a sling; men guide it with hands on the barrel",
   "Morning sun", "Tackle squeal, rope strain, shouts",
   dict(scene="pier", mood="nyday", ship=True, people=[dict(x=0.45, y=0.72, h=0.22, view="3q_r", hat="cap", arms=[(-1, 0, -0.3), (1, 0.1, -0.3)])]),
   card=("l", "MARY CELESTE", "Brigantine, 282 tons"))
sh(41, "MS · 50mm", "push_slow", "Slow push",
   "Briggs at the cabin table writing a letter",
   "Warm lamp + window light", "Pen nib, distant clatter of loading",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, people=[P(0.2, 2.5, "3q_l", pose="sit", beard=True)]),
   card=("r", "BENJAMIN BRIGGS", "Captain, Mary Celeste"))
sh(41, "OTS insert · 50mm", "static", "Over his shoulder",
   "Briggs (head and shoulder in frame) writes; the nib moves across the page",
   "Warm lamp", "Nib scratch, ink dip", INS("pen", mood="warm", arm_to=(0.6, 0.55), surface=(160, 120)))
sh(42, "WS · 35mm", "track_r", "Track along the pier with him",
   "Briggs on the pier studies her waterline, hands behind his back, a small approving nod",
   "Morning sun, long shadows", "Water lapping the piles, gulls",
   dict(scene="pier", mood="nyday", barrels=False, people=[dict(x=0.6, y=0.9, h=0.45, view="left", arms=[(-1, 0.05, 0.3), (1, -0.05, 0.3)])]))
sh(43, "MCU · 85mm", "static", "Locked",
   "Briggs looks up into the rigging, thoughtful",
   "Morning sun, side light", "Rigging creak",
   FACE(mood="nyday", bg="sea", beard=True, view="3q_r", light="r"))
sh(44, "WS · 28mm", "push_slow", "Slow push into the cabin",
   "Sarah seated; Sophia on the floor beside her with a doll",
   "Warm lamp", "Child's babble (no words), creak",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, organ=True,
       people=[P(-0.3, 2.6, "3q_r", pose="sit", female=True), P(0.4, 2.3, "3q_l", h=0.85, child=True, pose="sit")]),
   card=("r", "SARAH BRIGGS", "Captain's wife"))
sh(44, "CU · 85mm", "static", "Locked",
   "Sophia (face in frame) holds her doll up to her mother",
   "Warm lamp", "Soft giggle, rustle",
   FACE(mood="warm", bg="warm", child=True, female=True, s=0.38, view="3q_r", light="r"))
sh(45, "WS · 35mm", "push_slow", "Slow push",
   "Massachusetts: Arthur (7) at a window in his grandmother's house",
   "Cool autumn daylight through the window", "Clock tick, wind outside",
   dict(scene="home", mood="home", snow=False, people=[P(0.6, 3.0, "3q_r", h=1.2, child=True)]),
   card=("l", "MARION", "Massachusetts"))
sh(46, "MS · 50mm", "static", "Locked",
   "Arthur at a school desk writes on his own slate (callback to the ship's slate)",
   "Classroom window light", "Slate pencil squeak, children murmur",
   dict(scene="modern", mood="home", parts=False, people=[P(0.0, 2.5, "front", h=1.2, child=True, pose="sit")]))
sh(47, "CU · 85mm", "push_slow", "Slow push",
   "Briggs pauses mid-letter; a small, sad smile",
   "Warm lamp", "Pen stops; creak",
   FACE(mood="warm", bg="warm", beard=True, view="3q_l", light="r", expr="tired"))
sh(48, "WS · 24mm", "pan_r", "Pan across the cramped cabin",
   "Briggs looks around: bunk, organ, Sophia's things; no corner left for a boy",
   "Warm lamp", "Light creak; a wry exhale",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, organ=True, chest=True, people=[P(-0.4, 3.0, "3q_r", beard=True)]))
sh(49, "TOP-DOWN · maquette", "static", "Top-down cutaway of the cabin layout (white maquette)",
   "The aft cabin from above: every corner used",
   "Neutral studio light", "Muffled pier noise through the deck",
   CAB(mood="maq", cam=dict(hz=-0.3, camH=5), skylight=False, wet=False, organ=True, chest=True))
sh(50, "LOW MS · 28mm", "tilt_u", "From inside the cabin, tilt up the companionway",
   "A woman visitor comes down; her bonnet brim knocks the low beam; she ducks, laughing; Sarah rises to greet her",
   "Daylight from above, warm cabin", "Straw brim taps wood, skirts rustle, laughter",
   CAB(mood="warm", skylight=True, wet=False, people=[P(0.6, 3.0, "3q_l", female=True, hat="bonnet", pose="bend"), P(-0.5, 2.4, "3q_r", female=True)]))
sh(51, "WS · 24mm", "track_l", "Track along the gangway",
   "Stevedores roll barrels up the ramp; one is lowered into the hold in a sling",
   "Morning sun", "Barrels rumble on planks, tackle, shouts",
   dict(scene="pier", mood="nyday", people=[dict(x=0.6, y=0.75, h=0.25, view="3q_l", hat="cap", pose="bend"), dict(x=0.75, y=0.88, h=0.3, view="back", hat="cap", pose="bend")]))
sh(51, "MS · 50mm", "static", "Locked",
   "A tally clerk chalks the count on a board on the pier (real chalk strokes); his face in frame",
   "Morning sun", "Chalk strokes",
   INS("slate", mood="nyday", side="r", arm_to=(0.6, 0.58), hat="cap", surface=(170, 140)))
sh(51, "MS · 35mm · hold", "tilt_d", "Tilt down into the hold",
   "Men stow barrels in tiers by lantern; the hold fills toward the deck beams",
   "Lantern + hatch light shaft", "Heavy thuds, wood knocks, men grunt",
   dict(scene="hold", mood="warm", lantern=True, people=[dict(x=0.4, y=0.98, h=0.45, view="back", hat="cap", pose="bend")]))
sh(52, "MS · 50mm", "static", "Locked",
   "Sarah writing at the table flinches at a bang overhead and looks up",
   "Warm lamp", "Deck bang, pen stops",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, people=[P(0.0, 2.4, "3q_l", pose="sit", female=True)]))
sh(53, "CU · 50mm", "handheld", "Handheld",
   "A stevedore (head and arms in frame) mallets a bung home",
   "Hold lantern", "Mallet thud", dict(scene="hold", mood="warm", lantern=True, light=False,
   people=[dict(x=0.5, y=1.4, h=1.1, view="3q_r", hat="cap", arms=[(-1, 0.1, 0.2), (1, 0.3, -0.25)])]))
sh(53, "CU · 85mm", "static", "Locked",
   "Sarah presses her fingers to her temple, a small exasperated smile",
   "Warm lamp", "Muffled banging", FACE(mood="warm", bg="warm", female=True, view="3q_l", light="r", expr="tired"))
sh(54, "WS · 24mm", "track_r", "Track with her as she leaves the pier",
   "A steam tug tows the Mary Celeste off the pier into the river",
   "Cool morning", "Tug whistle, paddle wheel, river traffic",
   SEA(mood="nyday", ships=[MC(0.55, 0.35, sails="bare")], hy=0.55, coast=(0.5, 1.2, 0.05, 120), sky=(225, 200), sea=(140, 90)),
   tag="NOVEMBER 5, 1872")
sh(54, "WS · 35mm", "static", "Locked",
   "She rides at anchor off Staten Island; anchor chain runs out",
   "Grey, overcast", "Anchor chain rattles out, splash",
   SEA(mood="noon", ships=[MC(0.45, 0.3, sails="bare")], island=(0.7, 0.5, 0.05, 110)),
   card=("l", "STATEN ISLAND", "New York Harbor"))
sh(55, "MCU · 50mm", "static", "Locked; wind into the lens",
   "Briggs watches the pennant stream the wrong way; a small shrug",
   "Grey, gusty", "Gusts, pennant flutter",
   FACE(bg="sea", beard=True, view="3q_l", light="l"))
sh(56, "MS · 50mm", "push_slow", "Slow push",
   "Evening: Sarah writing by lamplight; Sophia asleep in the bunk behind her",
   "Warm lamp, dark corners", "Pen, slow creak, wind shifting outside",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, people=[P(0.2, 2.4, "3q_l", pose="sit", female=True), P(-1.1, 3.0, "front", h=0.6, child=True, pose="sit")]),
   tag="NOVEMBER 7, 1872")
sh(57, "WS · 35mm", "static", "Locked",
   "Crew heave at the windlass; the anchor comes up",
   "Morning, wind fair", "Windlass pawls clack, chain, men chant",
   DECK(cam=dict(hz=0.45, camH=1.3), masts=(6,), people=[P(-0.6, 3.0, "3q_r", pose="bend", **CAP), P(0.6, 3.2, "3q_l", pose="bend", **CAP)]))
sh(58, "MS · 50mm", "static", "Locked",
   "Sarah hands her letter to the pilot at the rail; he tucks it inside his coat (both fully in frame)",
   "Morning light", "Paper, wind",
   SEA(mood="nyday", fg="rail", sky=(225, 200), sea=(140, 90), people=[dict(x=0.35, y=1.02, h=0.62, view="3q_r", female=True, arms=[(-1, 0, 0.3), (1, 0.2, 0.05)]),
                                                                     dict(x=0.62, y=1.02, h=0.64, view="3q_l", hat="top", arms=[(-1, -0.2, 0.05), (1, 0, 0.3)])]))
sh(58, "WS · 35mm", "static", "Locked",
   "The pilot boat pulls away; the Mary Celeste sets sail behind it",
   "Morning haze", "Oars, sails filling",
   SEA(mood="nyday", ships=[MC(0.65, 0.3, sails="full")], boats=[dict(x=0.3, y=0.78, L=0.12, people=2)], sky=(225, 200), sea=(140, 90)))
sh(None, "WS · 35mm", "static", "Locked (2 s)", "The boat rows on toward shore",
   "Haze", "SILENCE before the line: oars only", SEA(mood="nyday", ships=[MC(0.7, 0.2, sails="full")], boats=[dict(x=0.3, y=0.75, L=0.09, people=2)], sky=(225, 200), sea=(140, 90)),
   dur=2.0, silence=True)
sh(59, "EWS · 50mm", "push_slow", "Very slow push",
   "She sails out into the haze, getting smaller",
   "Haze", "Wind, sea; music sustains", SEA(mood="nyday", ships=[MC(0.6, 0.1, sails="full")], fog=1, sky=(225, 200), sea=(140, 90)), w=1.4)

# ======================================================================
# 25 NOVEMBER — SANTA MARIA
# ======================================================================
sh(60, "EWS · 24mm", "track_r", "Low track alongside at dawn",
   "Mary Celeste under sail; Santa Maria low on the horizon",
   "Dawn, warm low sun behind cloud", "Dawn wind, bow wash",
   SEA(mood="dawn", ships=[MC(0.4, 0.34, sails="full")], island=(0.78, 0.22, 0.04, 120), **SKY_DAWN),
   tag="NOVEMBER 25, 1872 · OFF THE AZORES")
sh(61, "MS · 35mm", "static", "Locked",
   "Two crewmen at the bow; one points (arm with his body); Briggs behind with a telescope",
   "Dawn rim light", "Wind, a short laugh",
   SEA(mood="dawn", fg="bow", island=(0.75, 0.25, 0.04, 120), **SKY_DAWN,
       people=[dict(x=0.25, y=1.05, h=0.6, view="back", hat="cap", arms=[(-1, 0, 0.3), (1, 0.4, -0.25)]), dict(x=0.85, y=1.05, h=0.62, view="3q_l", arms=[(-1, -0.1, -0.1), (1, 0.05, 0.3)])]))
sh(61, "POV · telescope", "push_slow", "POV through the telescope (lens vignette)",
   "Cliffs of Santa Maria", "Dawn", "Telescope tube click, wind",
   SEA(mood="dawn", island=(0.5, 0.8, 0.12, 110), **SKY_DAWN))
sh(62, "OTS insert · 50mm", "static", "Over his shoulder",
   "The mate (head and shoulder in frame) chalks the morning entry on the slate",
   "Dawn port light", "Chalk scratching",
   INS("slate", mood="dawn", arm_to=(0.52, 0.55), hat="cap", ps=0.22), w=1.3)
sh(62, "ECU · macro", "static", "Locked",
   "The last chalk stroke; he sets the chalk down",
   "Dawn", "Chalk tap",
   INS("slate", mood="dawn", side="r", arm_to=(0.72, 0.7), hat="cap", ps=0.32))
sh(63, "MS · 50mm", "static", "Locked (time passes: light moves across the table)",
   "The slate on the table; nothing more is written",
   "Dawn shaft sliding across", "Room tone, creak",
   CAB(mood="dawn", slate=True, wet=False, skylight=True))
sh(64, "LOW · 24mm", "push_slow", "Slow push through the rail gap (callback)",
   "Open sea; the island far off; empty water",
   "Dawn", "Wind, waves",
   SEA(mood="dawn", fg="gap", island=(0.5, 0.2, 0.03, 120), **SKY_DAWN))

# ======================================================================
# WHAT'S MISSING
# ======================================================================
sh(65, "WS · 28mm", "static", "Locked",
   "Back to 4 December: Deveau in the captain's cabin opens cupboards one by one",
   "Cold skylight shaft", "Cupboard latches, drawers",
   CAB(people=[P(0.8, 2.8, "3q_r", **CAP)], water=True))
sh(66, "OTS insert · 50mm", "push", "Over his shoulder",
   "Deveau opens the chronometer box: an empty, shaped bed",
   "Cold", "Brass latch click",
   INS("chrono_box", arm_to=(0.45, 0.55), hat="cap", ps=0.2))
sh(66, "MS · 50mm", "static", "Flashback, locked",
   "Briggs winds the chronometer in its box, checks his watch against it",
   "Warm lamp (flashback)", "Winding key ratchet, tick",
   INS("chrono_box", mood="warm", arm_to=(0.5, 0.55), side="r", surface=(160, 120), ps=0.2))
sh(67, "MS · 35mm", "static", "Flashback, locked",
   "Briggs on deck takes a noon sight with the sextant (whole upper body in frame)",
   "Bright sun, warm (flashback)", "Sextant arm click, wind",
   SEA(mood="dawn", fg="rail", people=[dict(x=0.5, y=1.05, h=0.7, view="3q_r", arms=[(-1, 0.1, -0.15), (1, 0.15, -0.18)])], **SKY_DAWN))
sh(67, "OTS insert · 50mm", "static", "Locked",
   "Back to Deveau: the sextant case is empty",
   "Cold", "Case lid", INS("sextant_case", arm_to=(0.45, 0.55), hat="cap", ps=0.2))
sh(68, "OTS insert · 50mm", "static", "Locked",
   "Deveau pulls open the drawer where the ship's papers were kept",
   "Cold", "Drawer slide", INS("drawer", arm_to=(0.45, 0.6), hat="cap", ps=0.18))
sh(69, "MS · 35mm", "static", "Locked",
   "Deveau opens a locker: Briggs's coats still hang there, swaying with the roll",
   "Cold", "Hangers creak",
   INS("coats", side="l", arm_to=(0.42, 0.45), hat="cap", ps=0.3, surface=(120, 80)))
sh(70, "TOP-DOWN · maquette", "orbit", "Top-down white maquette, slow rotate",
   "The ship as a white maquette; the empty places lit by small warm pools of light",
   "Neutral studio + warm pools", "Low drone",
   dict(scene="xray", mood="maq", water=0, barrels=False, pumps=False), w=1.2)
sh(71, "CU · 50mm", "push_slow", "Slow push", "The empty boat chocks", "Warm pool on white", "Drone",
   INS("chocks", mood="maq", side=None, ps=0.2))
sh(72, "CU · 50mm", "push_slow", "Slow push", "The empty chronometer box and sextant case side by side", "Warm pool", "Drone",
   INS("chrono_box", mood="maq", side=None, ps=0.18, px=0.38, extra=[dict(prop="sextant_case", x=0.68, y=0.6, s=0.18)]))
sh(73, "CU · 50mm", "push_slow", "Slow push", "The empty drawer", "Warm pool", "Drone",
   INS("drawer", mood="maq", side=None, ps=0.2))
sh(None, "CU", "static", "Hold 1 s", "Black frame between the list and the rail", "—", "SILENCE (1 s)",
   dict(scene="black", mood="black"), dur=1.0, silence=True)
sh(74, "LOW · 24mm", "push", "Push through the rail gap (callback to shot 016)",
   "The gap in the rail and the sea beyond", "Overcast", "Wave wash through the gap",
   SEA(fg="gap", **SKY_NOON))
sh(75, "WS · 35mm", "static", "Reconstruction, locked, desaturated",
   "Figures (faces turned away) lower a boat through the gap; one passes a box down",
   "Grey, desaturated", "Muffled rope, voices without words",
   SEA(mood="spec", spec=True, fg="gap", boats=[dict(x=0.5, y=0.78, L=0.18, people=3)]), w=1.3)
sh(76, "MCU · 85mm", "push_slow", "Slow push",
   "Back to Deveau at the pump: determined", "Overcast", "Pump creak, wind",
   FACE(bg="sea", hat="cap", beard=True, expr="frown"), w=1.2)

# ======================================================================
# THE DECISION AND THE PASSAGE
# ======================================================================
sh(77, "OTS · 50mm", "static", "Over Deveau's shoulder onto Morehouse",
   "On the Dei Gratia: Morehouse speaks; warning in his face (no lip-sync, mouth hidden by angle)",
   "Overcast", "Wind, the Dei Gratia's rigging",
   FACE(bg="sea", hat="cap", beard=True, cx=0.62, s=0.34, view="3q_l", expr="worry", second=dict(cx=0.12, cy=0.5, s=0.55, view="back", hat="cap", tone=20)))
sh(77, "OTS · 50mm", "static", "Reverse over Morehouse onto Deveau",
   "Deveau listens", "Overcast", "Wind",
   FACE(bg="sea", hat="cap", beard=True, cx=0.38, s=0.34, view="3q_r", light="r", second=dict(cx=0.88, cy=0.5, s=0.55, view="back", hat="cap", tone=20)))
sh(78, "WS · 28mm", "track_r", "Track along the Dei Gratia deck",
   "Her own small crew at work; gaps where men will be missing",
   "Overcast", "Rigging, footsteps",
   DECK(masts=(8, 16), people=[P(-1.5, 5, "3q_r", pose="bend", **CAP), P(1.6, 7, "back", **CAP)]))
sh(79, "CU · 85mm", "push_slow", "Push; he turns out of frame",
   "Deveau decides and turns away", "Overcast", "One footstep, music beat",
   FACE(bg="sea", hat="cap", beard=True, view="left", light="l"))
sh(80, "MS · 35mm", "static", "Locked",
   "Deveau and two sailors pass down a box of instruments and a food sack into the boat",
   "Overcast", "Thuds, sack, oarlock",
   SEA(fg="rail", people=[dict(x=0.3, y=1.02, h=0.62, view="3q_r", hat="cap", pose="bend"), dict(x=0.52, y=1.03, h=0.6, view="back", hat="cap", pose="bend"),
                          dict(x=0.72, y=1.02, h=0.62, view="3q_l", hat="cap")]), w=1.3)
sh(80, "OTS insert · 50mm", "static", "Locked",
   "Deveau sets his own sextant case down in the boat", "Overcast", "Wood on wood",
   INS("sextant_case", mood="noon", arm_to=(0.45, 0.55), hat="cap", ps=0.2))
sh(81, "MS · 35mm", "handheld", "Handheld",
   "Two sailors work the pump handles; water gushes across the deck to the scuppers",
   "Overcast", "Pump clank, gush, scupper gurgle",
   DECK(cam=dict(hz=0.5, camH=1.2), wet=True, masts=(5,), people=[P(-0.5, 2.8, "3q_r", pose="bend", **CAP), P(0.5, 2.8, "3q_l", pose="bend", **CAP)]), w=1.2)
sh(81, "LOW · 24mm", "tilt_u", "Tilt up as the sail rises",
   "The three men hoist the spare sail into place of the lost one",
   "Overcast, sky bright", "Halyard, canvas fills",
   SEA(ships=[MC(0.5, 0.8, y=1.3, sails="spare")], hy=1.0))
sh(82, "EWS · 24mm", "track_r", "Track alongside; light changes from day to day",
   "She makes way eastward with three men aboard", "Sun and cloud across days", "Wash, steady wind",
   SEA(ships=[MC(0.5, 0.35, sails="spare")]))
sh(82, "MAQUETTE · 50mm", "track_r", "Track along the maquette",
   "Deveau's pencil route crawling east toward Gibraltar (drawn by his hand, in frame)",
   "Work lamp", "Pencil on paper",
   dict(scene="relief", mood="maq", pins=[(0.55, 0.50)], route=[(0.55, 0.50), (0.75, 0.48)], ots=dict(side="r", arm_to=(0.76, 0.48))))
sh(83, "WS · 24mm", "handheld", "Handheld, spray hits the lens",
   "Night gale: she heels hard; a wave breaks over the deck", "Storm night, lightning flash", "Gale, thunder, timbers groan, sea over the deck",
   SEA(mood="storm", ships=[MC(0.5, 0.4, sails="bare")], rain=True, **SKY_STORM), w=1.2)
sh(83, "MCU · 50mm", "handheld", "Handheld",
   "Deveau at the wheel, soaked, rain lashing", "Storm, lightning rim", "Rain, wheel strain",
   FACE(mood="storm", bg="storm", hat="cap", beard=True, rain=True, expr="frown"))
sh(84, "POV · 85mm", "handheld", "Through rain", "The Rock faint in the rain, then lost", "Storm", "Wind roar",
   SEA(mood="storm", rock=(0.6, 0.35, 80), rain=True, fog=1, **SKY_STORM))
sh(85, "WS · 35mm", "static", "Locked",
   "She lies in the lee of the North African coast", "Dusk after the storm", "Quieter sea, chain",
   SEA(mood="dusk", ships=[MC(0.4, 0.25, sails="bare")], coast=(0.6, 0.9, 0.12, 80), sky=(200, 160), sea=(110, 50)))
sh(85, "WS · 35mm", "static", "Locked", "Then off the coast of Spain", "Grey morning", "Gulls return, swell",
   SEA(mood="noon", ships=[MC(0.55, 0.25, sails="spare")], coast=(0.3, 0.8, 0.10, 90)))
sh(86, "EWS · 24mm", "crane_d", "Crane down to the bay",
   "Gibraltar Bay: the Mary Celeste sails in; the Dei Gratia already at anchor", "Clear winter light", "Harbour bells, gulls, anchor chain",
   SEA(mood="gib", rock=(0.6, 0.7, 115), ships=[MC(0.3, 0.2, sails="spare"), DG(0.75, 0.15, sails="bare")], sky=(235, 210), sea=(150, 90)),
   w=1.2, tag="DECEMBER 13, 1872 · GIBRALTAR", card=("l", "GIBRALTAR", "British territory"))
sh(86, "MS · 50mm", "static", "Locked",
   "Morehouse on the Dei Gratia's deck watches her come in", "Clear light", "Gulls",
   FACE(mood="gib", bg="sea", hat="cap", beard=True, view="left", light="l"))
sh(87, "MS · 50mm", "push_slow", "Slow push",
   "Deveau writing a letter by lamplight, slumped", "Warm lamp", "Pen, exhausted breath",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, people=[P(0.0, 2.4, "3q_l", pose="sit", **CAP)]))
sh(88, "CU · 85mm", "static", "Locked",
   "Deveau rubs his eyes with the heel of his hand (head and hand in frame)", "Warm lamp", "Long exhale",
   FACE(mood="warm", bg="warm", hat="cap", beard=True, expr="tired"))
sh(89, "OTS insert · 50mm", "static", "Locked",
   "Deveau's pen pauses; a small smile; he writes again", "Warm lamp", "Pen", INS("pen", mood="warm", arm_to=(0.6, 0.55), hat="cap", surface=(160, 120)))

# ======================================================================
# GIBRALTAR — THE COURT
# ======================================================================
sh(90, "WS · 35mm", "static", "Locked",
   "Court officers board the Mary Celeste at anchor", "Clear winter light", "Boat bump, boots",
   DECK(mood="gib", people=[P(-0.5, 5, "3q_r", hat="top"), P(0.6, 6, "3q_l", hat="top")], masts=(9,)), w=1.2)
sh(90, "CU · 50mm", "static", "Locked",
   "An officer (face in frame) nails the arrest notice to the mainmast", "Clear light", "Hammer blows",
   INS("notice", mood="gib", side="r", arm_to=(0.56, 0.4), ps=0.25, surface=(150, 110)))
sh(91, "WS · 24mm", "static", "Locked",
   "Vice Admiralty Court: Deveau and the Dei Gratia's crew on a bench", "Warm window light, dust in the air", "Room tone, rustle, coughs",
   dict(scene="court", mood="court", people=[P(-2.8, 5.8, "3q_r", pose="sit", **CAP), P(-2.2, 5.8, "3q_r", pose="sit", **CAP), P(-1.6, 5.8, "3q_r", pose="sit", **CAP)]))
sh(92, "MS · 50mm", "static", "Locked",
   "Deveau gives evidence; a clerk writes it down", "Window light", "Quill scratch",
   dict(scene="court", mood="court", people=[P(-0.5, 4.5, "front", **CAP), P(1.6, 5.0, "3q_l", pose="sit")]))
sh(93, "LOW MS · 35mm", "push_slow", "Low, slow push",
   "Flood rises from his table", "Window light behind", "Chair scrape, robe rustle",
   dict(scene="court", mood="court", people=[P(0.3, 4.0, "front", hat="wig")]), w=1.2,
   card=("r", "FREDERICK SOLLY FLOOD", "Attorney General, Gibraltar"))
sh(94, "CU · 85mm", "push_slow", "Slow push to the eyes",
   "Flood looks across at Deveau", "Side window light", "Clock tick; room falls quiet",
   FACE(mood="court", bg="court", hat="wig", view="3q_r", light="l", expr="frown"))
sh(94, "CU · 85mm", "static", "Reverse, locked",
   "Deveau holds his gaze", "Side light", "Clock tick",
   FACE(mood="court", bg="court", hat="cap", beard=True, view="3q_l", light="r"))
sh(95, "WS · 35mm", "static", "Locked",
   "Flood on the Mary Celeste's deck points out spots to a surveyor (arm with his body)", "Clear light", "Gulls, harbour",
   DECK(mood="gib", people=[P(-0.5, 4, "3q_r", hat="top", arms=[(-1, 0, 0.3), (1, 0.4, -0.1)]), P(0.6, 5, "3q_l", hat="top")], masts=(9,)))
sh(96, "UNDERWATER · 24mm", "track_l", "Track with the diver",
   "A helmet diver walks along under the hull, hand on the planks", "Green filtered daylight", "Air pump hiss, bubbles, muffled water",
   dict(scene="under", mood="under"), w=1.2)
sh(97, "CU · 50mm", "static", "Locked",
   "The diver (helmet in frame) runs his glove along the bow: no damage", "Green light", "Bubbles",
   dict(scene="under", mood="under", hull=True))
sh(98, "MS · 50mm", "static", "Locked",
   "The surveyor stops writing in his notebook and shakes his head", "Clear light", "Pencil stops, wind",
   FACE(mood="gib", bg="sea", hat="top", view="3q_r", light="r", expr="worry"))
sh(99, "MS · 35mm", "static", "Locked",
   "Flood kneels on the deck with a magnifying glass", "Clear light", "Knee on wood",
   DECK(mood="gib", cam=dict(hz=0.45, camH=1.0), people=[P(0.2, 2.6, "3q_l", pose="kneel", hat="top")], masts=(8,)))
sh(100, "OTS insert · 50mm", "push", "Over Flood's shoulder",
   "Dark stains soaked into the deck grain (real stains in the wood, not decals)", "Clear light", "Wind",
   INS("stain", mood="gib", bg="deck", arm_to=(0.45, 0.6), hat="top", ps=0.3))
sh(101, "MS · 35mm", "static", "Locked",
   "An officer slides a sword from under the captain's berth and hands it to Flood", "Skylight", "Scabbard scrape",
   CAB(mood="gib", wet=False, people=[P(-0.6, 2.6, "3q_r", pose="kneel", hat="top"), P(0.5, 3.0, "3q_l", hat="top")]))
sh(102, "MS · 50mm", "static", "Flashback 4 Dec, locked",
   "Deveau draws the sword from its sheath and looks along the blade", "Cold skylight", "Blade rasp",
   INS("sword", side="l", arm_to=(0.4, 0.6), hat="cap", ps=0.15))
sh(103, "CU · 85mm", "rack", "Rack from blade to his eyes",
   "Rust bloom on the blade; Deveau's face behind it", "Cold", "End of the rasp",
   INS("sword", side="r", arm_to=(0.75, 0.55), hat="cap", ps=0.2))
sh(104, "MS · 50mm", "static", "Locked",
   "A chemist at his bench scrapes a stain sample into a dish; the sword on the bench", "Window light", "Scraping, glass clink",
   dict(scene="lab", mood="lab", people=[P(0.2, 2.9, "front", pose="bend")]))
sh(None, "CU · 85mm", "static", "Locked (1.5 s)",
   "The chemist (face in frame) holds a test tube to the window", "Window light", "SILENCE before the reveal",
   INS("tube", mood="lab", side="r", arm_to=(0.5, 0.75), ps=0.25, surface=(170, 140)), dur=1.5, silence=True)
sh(105, "CU · 85mm", "static", "Locked",
   "No colour change; he sets the tube down", "Window light", "Glass on wood",
   INS("tube", mood="lab", side="r", arm_to=(0.5, 0.75), ps=0.25, surface=(170, 140)))
sh(106, "WS · 24mm", "static", "Locked; light moves across days",
   "The courtroom over months: papers pile on the clerk's desk", "Window light shifts", "Clock tick, quill, rain on glass",
   dict(scene="court", mood="court", piles=True, people=[P(1.6, 5.0, "3q_l", pose="sit")]))
sh(107, "MS · 50mm", "push_slow", "Slow push",
   "The judge reads the award; Deveau listens on the bench", "Window light", "Paper rustle, murmur (no gavel: British court)",
   dict(scene="court", mood="court", people=[P(0.0, 10.2, "front", h=1.0, Y=1.4, hat="wig"), P(-2.2, 5.8, "3q_r", pose="sit", **CAP)]))
sh(108, "CU · 85mm", "static", "Locked",
   "Flood sits back slowly", "Side light", "Chair creak",
   FACE(mood="court", bg="court", hat="wig", view="3q_r", light="l", expr="tired"))
sh(109, "WS · 35mm", "static", "Locked",
   "A new crew carries sea chests aboard; a new captain at the gangway", "Clear light", "Harbour, boots, chests",
   DECK(mood="gib", masts=(9,), people=[P(-0.5, 4, "3q_r", pose="bend", **CAP), P(0.7, 5, "3q_l", hat="top")]), w=1.2)
sh(110, "EWS · 24mm", "track_r", "Track as she sails",
   "The Mary Celeste sails out past the Rock", "Bright winter sun", "Sails fill, wind; music lifts",
   SEA(mood="gib", rock=(0.7, 0.6, 115), ships=[MC(0.35, 0.3, sails="full")], sky=(235, 210), sea=(150, 90)))

# ======================================================================
# GENOA — THE BARRELS
# ======================================================================
sh(111, "WS · 24mm", "static", "Locked",
   "Genoa: stevedores roll barrels off the Mary Celeste onto the quay", "Warm Italian daylight", "Harbour bells, barrels rumble",
   dict(scene="pier", mood="genoa", people=[dict(x=0.62, y=0.85, h=0.3, view="3q_l", hat="cap", pose="bend")]), w=1.3,
   tag="1873 · GENOA", card=("l", "GENOA", "Italy"))
sh(111, "MS · 50mm", "static", "Locked",
   "A stevedore lifts a barrel; it is far too light and he staggers", "Daylight", "Hollow knock",
   dict(scene="pier", mood="genoa", ship=False, people=[dict(x=0.45, y=0.95, h=0.6, view="3q_r", hat="cap", arms=[(-1, 0.1, -0.1), (1, 0.15, -0.12)])]))
sh(None, "WS · 35mm", "static", "Locked (1.5 s)", "The empty barrels set apart on the quay", "Daylight", "SILENCE before the number",
   dict(scene="pier", mood="genoa", ship=False, people=[]), dur=1.5, silence=True)
sh(111, "WS · 35mm", "push_slow", "Slow push",
   "Nine barrels in a row; a clerk (in frame) chalks a mark on each (real chalk)", "Daylight", "Hollow knocks, chalk",
   dict(scene="pier", mood="genoa", ship=False, people=[dict(x=0.3, y=0.92, h=0.5, view="3q_r", hat="cap", pose="bend")]))
sh(112, "CU · 50mm", "push", "Push in on one barrel",
   "One empty barrel", "Daylight", "Low drone",
   dict(scene="hold", mood="genoa", light=True), w=1.3)
sh(113, "X-RAY · maquette", "push_slow", "Slow push into the cutaway hold",
   "A barrel seam weeps; vapour gathers low in the hold", "Neutral; vapour glows", "Drip, faint hiss",
   dict(scene="xray", mood="maq", vapor=True, seep=True))
sh(114, "MS · 50mm", "static", "Reconstruction, locked",
   "A crewman's lantern in the hold; he recoils from the haze (face turned)", "Lantern, desaturated", "Lantern creak, tension rise",
   dict(scene="hold", mood="spec", spec=True, lantern=True, vapor=True, people=[dict(x=0.6, y=1.0, h=0.55, view="3q_l", hat="cap")]))
sh(115, "WS · 28mm", "handheld", "Reconstruction, handheld, low light",
   "Crew hurry on deck (back views, motion blur); Briggs gives orders", "Desaturated", "Muffled shouts, running feet",
   DECK(mood="spec", spec=True, people=[P(-0.8, 5, "back", **CAP), P(0.4, 6, "back", **CAP), P(1.2, 4, "3q_l", beard=True)]), w=1.4)
sh(116, "WS · 35mm", "static", "Locked",
   "Back to 4 December: the hatches as Deveau found them", "Overcast", "Wind",
   DECK(hatches=[(1.2, 6, 7.5, False)], masts=(10,)))
sh(117, "MS · 50mm", "static", "Locked",
   "Deveau opens the fore hatch and leans in, breathing in: nothing", "Overcast", "Hatch, breath",
   DECK(cam=dict(hz=0.45, camH=1.0), hatches=[(0.6, 2.4, 3.4, True)], masts=(), people=[P(-0.4, 2.6, "3q_r", pose="kneel", **CAP)]))
sh(118, "TOP-DOWN · 35mm", "static", "Locked top-down",
   "The main hatch still battened, tarpaulin and wedges in place; Deveau's boots beside", "Overcast", "Wind on canvas",
   DECK(cam=dict(hz=-0.4, camH=8), hatches=[(0, 6, 9, False)], sea=False, masts=()))
sh(119, "MACRO · cooper's bench", "push_slow", "Macro slide across the end grain",
   "A cooper (in frame) lays two stave sections side by side: red oak with open pores, white oak closed", "Warm workshop light", "Knife on wood",
   INS("staves", mood="genoa", side="l", arm_to=(0.3, 0.68), hat="cap", ps=0.25, surface=(160, 120)), w=1.3)
sh(119, "MACRO", "static", "Locked macro",
   "Liquid wicks into the red oak end grain", "Warm", "Faint seep",
   INS("staves", mood="genoa", side=None, ps=0.4, px=0.5))
sh(120, "WS · 35mm", "static", "Locked", "The nine barrels on the quay", "Daylight", "Harbour",
   dict(scene="pier", mood="genoa", ship=False))
sh(121, "WS · 24mm", "pull", "Slow pull back from the barrels to the whole harbour",
   "Barrels, quay, ships, city", "Daylight", "Harbour bed swells",
   dict(scene="pier", mood="genoa", ship=True), w=1.5)

# ======================================================================
# THE PUMP
# ======================================================================
sh(122, "MS · 35mm", "static", "Flashback 4 Dec, locked",
   "Deveau crouches by the pumps", "Overcast", "Wind",
   DECK(cam=dict(hz=0.5, camH=1.0), masts=(4,), people=[P(0.4, 2.4, "3q_l", pose="kneel", **CAP)]))
sh(123, "OTS insert · 50mm", "push", "Over his shoulder",
   "Pump parts laid out on the deck: plunger, leather valve, box", "Overcast", "Metal parts clink",
   INS("pump_parts", bg="deck", mood="noon", arm_to=(0.42, 0.6), hat="cap", ps=0.18))
sh(124, "WS · 24mm", "static", "Flashback, locked",
   "A shipyard: carpenters at the refit; coal dust stains in the hold", "Hazy daylight", "Saws, mallets, shovels on coal",
   dict(scene="shipyard", mood="nyday", people=[dict(x=0.3, y=0.92, h=0.35, view="3q_r", hat="cap", pose="bend")]))
sh(125, "MS · 50mm", "push_slow", "Slow push",
   "Present day: MacGregor at a desk under a lamp with copies of the court record", "Modern lamp, cool room", "Modern room tone, paper",
   dict(scene="modern", mood="modern", people=[P(0.0, 2.6, "3q_l", pose="sit", female=True)]), w=1.3,
   tag="2006", card=("r", "ANNE MacGREGOR", "Documentary researcher"))
sh(126, "MACRO · 100mm", "push_slow", "Macro inside the pump barrel",
   "Grit and coal dust packed around the valve leather", "Torch-like raking light", "Grit scrape",
   INS("pump_parts", mood="cold", side=None, ps=0.35, px=0.45))
sh(127, "MS · 50mm", "handheld", "Reconstruction, handheld",
   "A crewman kneels at the half-dismantled pump by lantern, frustrated", "Lantern, desaturated", "Spanner, rain",
   DECK(mood="spec", spec=True, cam=dict(hz=0.5, camH=1.0), masts=(4,), people=[P(0.3, 2.4, "3q_l", pose="kneel", **CAP)]), w=1.2)
sh(128, "CU · 50mm", "push_slow", "Slow push (callback)",
   "The parts on the deck as Deveau found them", "Overcast", "Wind thins",
   INS("pump_parts", bg="deck", mood="noon", side=None, ps=0.2))

# ======================================================================
# THE DRIFT TEST
# ======================================================================
sh(129, "WS · 35mm", "static", "Locked",
   "MacGregor and Richardson at a chart table with the court record open", "Modern lamp", "Paper",
   dict(scene="modern", mood="modern", people=[P(-0.6, 2.7, "3q_r", female=True), P(0.6, 2.8, "3q_l")]),
   card=("r", "PHIL RICHARDSON", "Oceanographer"))
sh(130, "OTS insert · 50mm", "static", "Over Richardson's shoulder",
   "He presses two brass pins into a large chart", "Lamp", "Pin taps",
   INS("chart", mood="modern", arm_to=(0.4, 0.55), ps=0.18, surface=(140, 120)))
sh(131, "ECU · macro", "rack", "Rack from pin to pin",
   "Pin at Santa Maria (soft orange band), then the pin where the Dei Gratia found her", "Lamp", "Two soft pulses",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.5)], ripple=(0.2, 0.56)), w=1.3)
sh(132, "OTS · 50mm", "track_r", "Track with the pencil",
   "Richardson (head and shoulder in frame) draws the drift line in pencil from pin to pin", "Lamp", "Pencil on paper",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.5)], line=[(0.2, 0.56), (0.32, 0.6), (0.44, 0.53)], ots=dict(side="r", arm_to=(0.45, 0.53))), w=1.2)
sh(132, "EWS · 24mm", "static", "Locked; sky moves (wind)",
   "Full scale: the empty ship drifting under her sails, nobody at the wheel", "Changing sky", "Wind, wash",
   SEA(ships=[MC(0.5, 0.3, sails="torn")]), w=1.2)
sh(None, "ECU · macro", "static", "Locked (1.5 s)", "The pencil tip nears the second pin", "Lamp", "SILENCE: pencil only",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.5)], line=[(0.2, 0.56), (0.32, 0.6), (0.44, 0.53), (0.52, 0.51)], ots=dict(side="r", arm_to=(0.53, 0.51))),
   dur=1.5, silence=True)
sh(133, "ECU · macro", "static", "Locked", "The line reaches it; the pencil lifts", "Lamp", "Pencil tap",
   dict(scene="relief", mood="maq", pins=[(0.2, 0.56), (0.55, 0.5)], line=[(0.2, 0.56), (0.32, 0.6), (0.44, 0.53), (0.55, 0.5)], ripple=(0.55, 0.5)))
sh(134, "EWS · 24mm", "push_slow", "Slow push (callback to dawn)",
   "The ship with Santa Maria in sight", "Dawn", "Wind",
   SEA(mood="dawn", ships=[MC(0.35, 0.3, sails="full")], island=(0.75, 0.22, 0.04, 120), **SKY_DAWN))
sh(135, "MS · 35mm", "handheld", "Reconstruction, handheld",
   "Night of rough weather: Briggs at the pump well with the sounding rod and a lantern", "Lantern, rain, desaturated", "Storm, rain, rod knock",
   DECK(mood="spec", spec=True, cam=dict(hz=0.45, camH=1.2), masts=(4,), wet=True, people=[P(0.3, 2.6, "3q_l", pose="bend", beard=True)]), w=1.3)
sh(135, "MS · 35mm", "handheld", "Reconstruction",
   "Crew at the pumps; the pump coughs and sputters", "Desaturated", "Pump gurgle, sputter",
   DECK(mood="spec", spec=True, cam=dict(hz=0.5, camH=1.2), masts=(5,), wet=True, people=[P(-0.5, 2.8, "3q_r", pose="bend", **CAP), P(0.5, 2.8, "3q_l", pose="bend", **CAP)]))
sh(136, "X-RAY · maquette", "tilt_d", "Tilt down through the packed cargo",
   "Barrels packed to the deck beams; the bottom of the hold hidden in the dark", "Neutral, bottom unlit", "Deep slosh",
   dict(scene="xray", mood="maq", water=0.12), w=1.3)
sh(137, "OTS · 50mm", "push_slow", "Over Briggs's shoulder, slow push to the island",
   "Briggs looks at Santa Maria on the horizon", "Dawn, desaturated", "Wind",
   SEA(mood="dawn", spec=True, island=(0.6, 0.25, 0.04, 120), fg="rail", people=[dict(x=0.15, y=1.15, h=0.95, view="back", tone=20)], **SKY_DAWN), w=1.3)

# ======================================================================
# WHAT WE DON'T KNOW
# ======================================================================
sh(138, "OTS · 50mm", "pull", "Pull back; colour drains", "Briggs's silhouette and the island", "Dawn fading to grey",
   "Wind drops", SEA(mood="spec", spec=True, island=(0.6, 0.25, 0.04, 120), fg="rail", people=[dict(x=0.15, y=1.15, h=0.95, view="back", tone=20)]))
sh(139, "ECU · macro", "static", "Callback to shot 049", "The wet line on Deveau's rod", "Overcast", "Drip",
   INS("rod", bg="deck", arm_to=(0.48, 0.52), hat="cap", mood="noon", ps=0.3))
sh(140, "ECU · macro", "static", "Reconstruction, locked, slow fade",
   "Briggs's rod in lantern light: the wet line out of focus, unreadable", "Lantern, desaturated", "Muffled",
   INS("rod", bg="deck", arm_to=(0.48, 0.52), mood="spec", spec=True, ps=0.3, ots_tone=15), blur=10, w=1.4)
sh(141, "WS · 35mm", "static", "Reconstruction, locked",
   "The boat in the water alongside, ten figures in it (faces away); a line runs to the ship", "Desaturated", "Water, creak",
   SEA(mood="spec", spec=True, ships=[MC(0.65, 0.5, sails="full", y=0.62)], boats=[dict(x=0.25, y=0.78, L=0.18, people=5)], hy=0.55))
sh(142, "CU · 50mm", "static", "Reconstruction",
   "A crewman in the boat holds the taut line tied to the ship's rail", "Desaturated", "Rope strain",
   SEA(mood="spec", spec=True, boats=[dict(x=0.4, y=0.95, L=0.6, people=3)], hy=0.45), w=1.4)
sh(143, "WS · 35mm", "static", "Locked",
   "A gust darkens the water; her sails fill and she gathers way", "Desaturated", "Gust, canvas boom",
   SEA(mood="spec", spec=True, ships=[MC(0.6, 0.4, sails="full")]))
sh(144, "WS · 24mm · high", "crane_u", "Crane up",
   "Distance opens between the rowing boat and the ship", "Desaturated", "Oars, wind",
   SEA(mood="spec", spec=True, ships=[MC(0.78, 0.18, sails="full")], boats=[dict(x=0.25, y=0.7, L=0.08, people=4)], hy=0.35))
sh(145, "EWS · 24mm", "push_slow", "Slow push into fog",
   "A tiny boat on grey sea; the ship far off; both fade into haze", "Grey", "Wind, then near-silence",
   SEA(mood="spec", spec=True, ships=[MC(0.8, 0.08, sails="full")], boats=[dict(x=0.35, y=0.6, L=0.04, people=3)], fog=1), w=1.4)

# ======================================================================
# LEGEND AND RECORD
# ======================================================================
sh(146, "MS · 35mm", "push_slow", "Stylised 'legend' version, slow push",
   "A warm candlelit table with steaming food and cups", "Sepia legend grade, candle", "Warm crackle, cutlery",
   CAB(mood="legend", legend=True, lamp=True, skylight=False, wet=False, bunk=False))
sh(147, "CU · 85mm", "push_slow", "Slow push", "Steam rising from a cup", "Candle", "Faint clink",
   CAB(mood="legend", legend=True, lamp=False, skylight=False, wet=False, bunk=False, cam=dict(hz=0.2, camH=1.2)))
sh(148, "MS · 35mm", "static", "Match-cut to the same frame in cold light",
   "The real table: soaked, water on the floor", "Cold skylight", "Drip, slosh",
   CAB(mood="cold", water=True, skylight=True, bunk=False), w=1.2)
sh(148, "WS · 24mm", "static", "Locked", "The galley with water in it", "Grey", "Slosh",
   dict(scene="galley", mood="cold"))
sh(149, "MS · 50mm", "push_slow", "Slow push (callback to shot 059)", "The slate on the table; its last line",
   "Cold", "Creak", CAB(mood="cold", slate=True, skylight=True, bunk=False), w=1.3)

# ======================================================================
# HOME
# ======================================================================
sh(150, "WS · 35mm", "static", "Locked",
   "Gibraltar: a consular clerk packs a crate", "Warm office light", "Straw, hammer",
   dict(scene="modern", mood="court", parts=False, people=[P(0.0, 2.7, "front", pose="bend")]))
sh(151, "OTS insert · 50mm", "static", "Over the clerk's shoulder",
   "He presses the consul's seal into hot wax on the parcel string", "Warm", "Wax press, seal lifts",
   INS("seal", mood="court", arm_to=(0.5, 0.55), ps=0.2, surface=(160, 120)))
sh(151, "WS · 35mm", "static", "Locked",
   "Massachusetts, winter: a carrier carries crates into the house", "Snow light", "Snow crunch, door, stamping boots",
   dict(scene="home", mood="home", crates=True, people=[P(-0.8, 3.0, "3q_r", hat="top", pose="bend")]))
sh(152, "MS · 50mm", "static", "Locked",
   "Arthur's grandmother lifts the lid; the small reed organ in straw", "Window snow light", "Crowbar, nails, straw",
   dict(scene="home", mood="home", organ=True, people=[P(0.6, 2.8, "3q_l", female=True, pose="bend")]))
sh(152, "OTS insert · 50mm", "static", "Locked", "She lifts out Benjamin's sword wrapped in cloth", "Window light", "Cloth, metal",
   INS("sword", mood="home", side="l", arm_to=(0.4, 0.6), female=True, ps=0.15, surface=(160, 120)))
sh(152, "OTS insert · 50mm", "static", "Locked", "Arthur lifts two dolls from the straw", "Window light", "Straw rustle",
   INS("dolls", mood="home", side="l", arm_to=(0.4, 0.62), ps=0.2, surface=(160, 120)))
sh(None, "ECU", "static", "Locked (1.5 s)", "Arthur's hands and face over the dolls", "Window light", "SILENCE: straw only",
   INS("dolls", mood="home", side="r", arm_to=(0.75, 0.6), ps=0.24, surface=(160, 120)), dur=1.5, silence=True)
sh(153, "ECU · 100mm", "push_slow", "Slow push",
   "One doll's arm is broken (callback to the hollow in the bunk)", "Window light", "Clock tick",
   INS("dolls", mood="home", side="r", arm_to=(0.75, 0.6), ps=0.3, px=0.48, surface=(160, 120)), w=1.3)
sh(154, "MS · 50mm", "push_slow", "Slow push",
   "Arthur at the window holding the doll; snow outside", "Snow light", "Clock, wind",
   dict(scene="home", mood="home", people=[P(0.9, 3.4, "3q_r", h=1.2, child=True)]))
sh(155, "MS · 50mm", "pan_r", "Callback: New York cabin; pan from Briggs writing to the empty corner",
   "Briggs writes; the corner where a boy might have slept", "Warm lamp", "Pen",
   CAB(mood="warm", lamp=True, skylight=False, wet=False, people=[P(-0.6, 2.5, "3q_r", pose="sit", beard=True)]), w=1.3)
sh(156, "WS · 24mm", "static", "Callback", "The ship at Gibraltar", "Clear light", "Harbour",
   SEA(mood="gib", rock=(0.6, 0.7, 115), ships=[MC(0.35, 0.2, sails="bare")], sky=(235, 210), sea=(150, 90)))
sh(157, "WS · 35mm", "static", "Callback", "The barrels on the quay at Genoa", "Daylight", "Harbour",
   dict(scene="pier", mood="genoa", ship=False))
sh(158, "MS · 50mm", "static", "Callback", "Arthur with the dolls", "Snow light", "Clock",
   dict(scene="home", mood="home", people=[P(0.2, 2.6, "3q_l", h=1.2, child=True, pose="sit")]))
sh(None, "EWS · 24mm · wave height", "static", "Locked (2.5 s)", "Empty ocean", "Grey, sun breaking", "SILENCE before the last line: waves only",
   SEA(clouds=True, **SKY_NOON), dur=2.5, silence=True)
sh(159, "EWS · 24mm · wave height", "push_slow", "Slow push toward the horizon; hold",
   "Nothing on the sea", "Grey with a break of light", "Wind, waves, fade",
   SEA(clouds=True, sun=(0.7, 0.3), **SKY_NOON), w=1.6)
sh(None, "BLACK", "static", "Fade to black (6 s)", "End", "—", "Waves fade to silence", dict(scene="black", mood="black"), dur=6.0)
