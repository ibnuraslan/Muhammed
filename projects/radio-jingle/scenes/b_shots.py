"""Chat B shot lists (Ch3-5), in film order: (set, move, label). Seconds are estimates (184 wpm) until the
voiceover arrives; the first shot of each chapter carries the title card and 3 s of picture before the voice.
  python b_shots.py            -> prints the lists with estimated seconds
"""
LEAD = 3.0
WORDS = {"ch3": 339, "ch4": 615, "ch5": 405}

CHAPTERS_V1 = {
    "ch3": [("b_woods", "wire", "3-1A Wire through the trees + title"), ("b_woods", "lookout", "3-1B Second lookout"),
            ("b_boxprint", "dust", "3-2A Print dusted on the box tape"), ("b_boxprint", "lift", "3-2B Powder on the strip"),
            ("b_archive", "aisle", "3-3A Card archive aisle"), ("b_archive", "match", "3-3B No match at the light table"),
            ("b_workshop", "solder", "3-4A TV repair bench"), ("b_workshop", "letters", "3-4B Unopened final notices"),
            ("b_home81", "game", "3-5A Board game evening"), ("b_home81", "search", "3-5B Next day: search finds nothing"),
            ("b_home81", "moped", "3-6A Moped with a spade"), ("b_home81", "curtain", "3-6B Landlord at the curtain"),
            ("b_interro", "question", "3-7A Questioning"), ("b_interro", "size", "3-7B He shows a size"),
            ("b_woods", "search", "3-8A Walked through the woods"), ("b_woods", "unsure", "3-8B He cannot find the spot"),
            ("b_interro", "retract", "3-9A Statement pushed back"), ("b_interro", "leave", "3-9B He walks out"),
            ("b_media", "appeal", "3-10A TV appeal"), ("b_media", "phones", "3-10B Tips by phone"),
            ("b_archive", "twelve", "3-11A Twelve cabinets"), ("b_archive", "tube", "3-11B The tapes, the light dims")],
    "ch4": [("b_dna", "swab", "4-1A DNA swab + title"), ("b_dna", "seq", "4-1B Sequencer peaks"),
            ("b_dna", "bags", "4-2A Screw and glass"), ("b_dna", "print", "4-2B The bags slid apart"),
            ("b_north", "quay", "4-3A Northern harbour"), ("b_north", "shop", "4-3B The shop"),
            ("b_media", "pin", "4-4A The deadline file"), ("b_media", "clock", "4-4B The clock"),
            ("b_north", "watch", "4-5A Surveillance"), ("b_north", "lock", "4-5B He locks up"),
            ("b_north", "boxes", "4-6A House search"), ("b_north", "saliva", "4-6B Saliva sample"),
            ("b_north", "steps", "4-7A Recorder carried out"), ("b_flea", "flea", "4-7B Flea-market memory"),
            ("b_dna", "orbit", "4-8A The recorder"), ("b_dna", "keys", "4-8B Keys and meter"),
            ("b_phonetics", "listen", "4-9A Phonetics expert"), ("b_phonetics", "segments", "4-9B Three calls"),
            ("b_phonetics", "eleven", "4-10A Eleven recorders"), ("b_phonetics", "pause", "4-10B The pause key"),
            ("b_north", "dawn", "4-11A Arrest at dawn"), ("b_north", "away", "4-11B Driven away"),
            ("b_court", "dock", "4-12A In court"), ("b_court", "witness", "4-12B The market seller"),
            ("b_michael", "read", "4-13A Michael reads the files"), ("b_michael", "lookup", "4-13B He looks up"),
            ("b_chain", "radio", "4-14A Recon: radio to recorder"), ("b_chain", "copy", "4-14B Recon: copied to cassette"),
            ("b_chain", "booth", "4-15A Recon: the phone booth"), ("b_chain", "mouth", "4-15B Recon: player to mouthpiece"),
            ("b_chain", "poles", "4-16A Recon: down the line"), ("b_hall", "line_end", "4-16B Recon: police recorder"),
            ("b_michael", "replay", "4-17A He replays the tape"), ("b_michael", "objection", "4-17B His objections")],
    "ch5": [("b_court", "bench", "5-1A The bench + title"), ("b_court", "exhibit", "5-1B The binoculars"),
            ("b_court", "rise", "5-2A All rise"), ("b_court", "back", "5-2B The verdict"),
            ("b_ch5", "fedwide", "5-3A Federal court"), ("b_ch5", "press", "5-3B Past the press"),
            ("b_ch5", "walk", "5-4A Michael, 2013"), ("b_ch5", "wait", "5-4B Waiting"),
            ("b_michael", "notes", "5-5A A few notes"), ("b_michael", "window", "5-5B Night"),
            ("b_ch5", "listen", "5-6A The physicist"), ("b_ch5", "year", "5-6B A year passes"),
            ("b_court", "civil", "5-7A Civil court"), ("b_ch5", "fog", "5-7B Boarding school in fog"),
            ("b_court", "lights", "5-8A Overturned"), ("b_court", "pullback", "5-8B Lights out"),
            ("b_ch5", "gate", "5-9A Released, 2023"), ("b_ch5", "wall", "5-9B Along the wall"),
            ("b_media", "scrub", "5-10A Broadcasters revisit"), ("b_media", "paused", "5-10B Paused"),
            ("b_hall", "offhook", "5-11 Nobody answered")],
}


# ------------------------------------------------------------------ storyboard v2 (review/STORYBOARD_v2.md)
# Each chapter has one long hero take (LONG) and short inserts around it. (set, move, label[, v1 label it replaces])
CHAPTERS = {
    "ch3": [("b_woods", "wire", "3-1 Wire drawn through the woods (long) + title", "3-1A"),
            ("b_void", "tape", "3-2A Print surfaces on the tape", "3-2A"), ("b_void", "cards", "3-2B Twenty thousand cards", "3-2B"),
            ("b_void", "compare", "3-3A No match", "3-3A"), ("b_village", "distance", "3-3B A few hundred meters", None),
            ("b_workshop", "solder", "3-4A TV repair bench", "3-4A"), ("b_workshop", "letters", "3-4B The letters keep coming", "3-4B"),
            ("b_home81", "game", "3-5A Alibi: the evening passes", "3-5A"), ("b_workshop", "nothing", "3-5B Search: nothing", "3-5B"),
            ("b_home81", "moped", "3-6A Moped with a spade", "3-6A"), ("b_home81", "curtain", "3-6B Landlord at the curtain", "3-6B"),
            ("b_interro", "offer", "3-7A The offer, on the table", "3-7A"), ("b_void", "soil", "3-7B The hole and the soil", "3-7B"),
            ("b_woods", "search", "3-8A Into the woods", "3-8A"), ("b_woods", "spots", "3-8B Every spot he points to", "3-8B"),
            ("b_interro", "strike", "3-9A Statement struck through", "3-9A"), ("b_interro", "leave", "3-9B He walks out", "3-9B"),
            ("b_tvstreet", "tvstreet", "3-10A One broadcast, every window", "3-10A"), ("b_media", "phones", "3-10B Tips by phone", "3-10B"),
            ("b_archive", "twelve", "3-11A Twelve numbered cabinets", "3-11A"), ("b_archive", "tube", "3-11B 1981 to 1989, on tape", "3-11B")],
    "ch4": [("b_void", "boxmarks", "4-1A The box, traces marked + title", "4-1A"), ("b_dna", "seq", "4-1B Sequencer peaks", "4-1B"),
            ("b_void", "string", "4-2A A thread from screw to glass", "4-2A"), ("b_void", "nolink", "4-2B No link", "4-2B"),
            ("b_north", "quay", "4-3A Northern harbour", "4-3A"), ("b_north", "shop", "4-3B The shop", "4-3B"), ("b_void", "timeline", "4-4 Thirty years, four left", "4-4A"),
            ("b_north", "watch", "4-5A Surveillance", "4-5A"), ("b_north", "lock", "4-5B He locks up", "4-5B"),
            ("b_north", "boxes", "4-6A House search", "4-6A"), ("b_north", "saliva", "4-6B Saliva sample", "4-6B"),
            ("b_north", "steps", "4-7A Recorder carried out", "4-7A"), ("b_flea", "flea", "4-7B Flea-market account", "4-7B"),
            ("b_dna", "orbit", "4-8A The recorder", "4-8A"), ("b_dna", "keys", "4-8B Keys and meter", "4-8B"),
            ("b_phonetics", "listen", "4-9A Phonetics expert", "4-9A"), ("b_void", "reels", "4-9B Three calls, one note drops", "4-9B"),
            ("b_void", "lineup", "4-10A Eleven recorders, a line-up", "4-10A"), ("b_void", "chosen", "4-10B The seized machine", "4-10B"),
            ("b_north", "dawn", "4-11A Arrest at dawn", "4-11A"), ("b_north", "away", "4-11B Driven away", "4-11B"),
            ("b_court", "dock", "4-12A In court", "4-12A"), ("b_flea", "empty", "4-12B Nobody recalls the sale", "4-12B"),
            ("b_michael", "read", "4-13A Michael reads the files", "4-13A"), ("b_michael", "memory", "4-13B Piano practice, that day", "4-13B"),
            ("b_void", "chain", "4-14 The chain on one table (long)", "4-14A"), ("b_void", "clicks", "4-16C Where did the click enter?", None),
            ("b_michael", "replay", "4-17A He replays the tape", "4-17A"), ("b_michael", "objection", "4-17B His objections", "4-17B")],
    "ch5": [("b_court", "bench", "5-1A The bench + title", "5-1A"), ("b_void", "exhibits", "5-1B The evidence, item by item", "5-1B"),
            ("b_void", "days56", "5-2C Fifty-six days", None),
            ("b_court", "rise", "5-2A All rise", "5-2A"), ("b_court", "back", "5-2B The verdict", "5-2B"),
            ("b_ch5", "fedwide", "5-3A Federal court", "5-3A"), ("b_ch5", "press", "5-3B Past the press", "5-3B"),
            ("b_ch5", "walk", "5-4A Michael, 2013", "5-4A"), ("b_ch5", "wait", "5-4B Waiting", "5-4B"),
            ("b_michael", "notes", "5-5A A few notes", "5-5A"), ("b_michael", "window", "5-5B The tone that never stops", "5-5B"),
            ("b_ch5", "listen", "5-6A The physicist", "5-6A"), ("b_ch5", "year", "5-6B A year passes", "5-6B"),
            ("b_court", "civil", "5-7A Civil court", "5-7A"), ("b_ch5", "fog", "5-7B Boarding school in fog", "5-7B"),
            ("b_court", "lights", "5-8A Overturned", "5-8A"), ("b_court", "pullback", "5-8B Lights out", "5-8B"),
            ("b_ch5", "gate", "5-9A Released, 2023", "5-9A"), ("b_ch5", "wall", "5-9B Along the wall", "5-9B"),
            ("b_media", "scrub", "5-10A Broadcasters revisit", "5-10A"), ("b_media", "paused", "5-10B Paused", "5-10B"),
            ("b_hall", "offhook", "5-11 Nobody answered (long)", "5-11")],
}
CHANGED = {"3-1", "3-2A", "3-2B", "3-3A", "3-3B", "3-4B", "3-5A", "3-5B", "3-7A", "3-7B", "3-8B", "3-9A", "3-10A", "3-11A", "3-11B",
           "4-1A", "4-2A", "4-2B", "4-4", "4-9B", "4-10A", "4-10B", "4-12B", "4-13B", "4-14", "4-16C", "5-1B", "5-2C", "5-5B", "5-11"}
LONG = {("b_woods", "wire"): 26.0, ("b_void", "chain"): 45.0, ("b_hall", "offhook"): 25.0}


def seconds(ch):
    """v2 estimate until the VO lands: long takes keep their length, the inserts share the rest of the chapter's words."""
    shots = CHAPTERS[ch]
    total = WORDS[ch] / 184 * 60
    fixed = sum(LONG.get((s[0], s[1]), 0.0) for s in shots)
    rest = [s for s in shots if (s[0], s[1]) not in LONG]
    each = max(2.0, (total - fixed) / max(1, len(rest)))
    out = []
    for k, s in enumerate(shots):
        sec = LONG.get((s[0], s[1]), each) + (LEAD if k == 0 else 0.0)
        out.append((s[0], s[1], s[2], round(sec, 2)))
    return out


def seconds_v1(ch):
    shots = CHAPTERS_V1[ch]
    total = WORDS[ch] / 184 * 60
    each = total / len(shots)
    out = []
    for k, s in enumerate(shots):
        sec = each + (LEAD if k == 0 else 0.0) + (2.0 if (ch == "ch5" and k == len(shots) - 1) else 0.0)
        out.append((*s, round(sec, 2)))
    return out


if __name__ == "__main__":
    for ch in CHAPTERS:
        rows = seconds(ch)
        print(ch, len(rows), "shots,", round(sum(r[3] for r in rows), 1), "s")
        for r in rows:
            print("  ", r)


# ------------------------------------------------------------------ storyboard frames: VO line and action per shot
VO = {
    "3-1": "Investigators eventually trace about a hundred and forty meters of green wire through the trees… views in opposite directions… How it was used that evening remains uncertain.",
    "3-2A": "Forensic investigators lift a fingerprint from adhesive tape on the box.",
    "3-2B": "As the inquiry expands, they will compare around twenty thousand fingerprints.",
    "3-3A": "They find no match for the print on the tape.",
    "3-3B": "One name comes up within days of the discovery. Werner Mazurek lives a few hundred meters from the Herrmanns.",
    "3-4A": "He's a trained mechanic with a television repair business…",
    "3-4B": "…and substantial debts.",
    "3-5A": "…he eventually says he was playing the board game Risk with his wife and two friends.",
    "3-5B": "An early search of his home and workshop turns up nothing that ties him to the crime.",
    "3-6A": "Then police speak to Klaus Pfaffinger… His landlord has reported seeing him with a spade strapped to his moped…",
    "3-6B": "…before the kidnapping.",
    "3-7A": "…Mazurek offered him a thousand marks and a color television to dig a hole in the woods.",
    "3-7B": "He says he dug it and later saw a box in it. Some of his details about the size of the hole and the soil will matter decades later.",
    "3-8A": "First, the detectives take him into the woods and ask him to show them the spot.",
    "3-8B": "He fails to lead them to it.",
    "3-9A": "Back at the police station, he retracts his story. He never repeats it in later interrogations.",
    "3-9B": "Police release him without charge.",
    "3-10A": "The investigation goes nationwide. A television appeal puts the case in front of viewers across West Germany.",
    "3-10B": "The tips keep coming.",
    "3-11A": "Eventually, the files on the leads fill twelve steel cabinets.",
    "3-11B": "By the end of the eighties, the investigation has slowed. The calls are still on tape.",
    "4-1A": "In the mid-2000s, investigators go back to the physical evidence. This time, they have DNA profiling.",
    "4-1B": "They recover several genetic profiles from traces on the box.",
    "4-2A": "In 2007, one from a screw appears to match a sample from a drinking glass in the apartment of a woman killed in Munich.",
    "4-2B": "…After further forensic work, the court in the Munich case finds no link between the two crimes.",
    "4-3A": "By 2007, Pfaffinger is dead. Mazurek has moved to northern Germany…",
    "4-3B": "…and sells boat accessories.",
    "4-4": "Investigators are running up against a deadline… a thirty-year limitation period… only a few years left to bring charges.",
    "4-5A": "Police put Mazurek under surveillance…",
    "4-5B": "(surveillance continues)",
    "4-6A": "…and search his home.",
    "4-6B": "They take a saliva sample. His DNA doesn't match the profiles recovered from the box.",
    "4-7A": "But police also take away something he says he bought at a flea market…",
    "4-7B": "…just weeks earlier.",
    "4-8A": "A reel-to-reel tape recorder.",
    "4-8B": "A Grundig TK Two Forty-Eight.",
    "4-9A": "A forensic phonetics specialist from the Bavarian state criminal police listens to the old calls.",
    "4-9B": "Of the recordings she examines, three contain the radio jingle… one of the highest notes drops in volume.",
    "4-10A": "She tests the Grundig… play button, the pause button… Investigators test eleven comparable recorders.",
    "4-10B": "The seized machine produces the combination the expert finds most persuasive… probably one of the devices used.",
    "4-11A": "Police arrest Mazurek in May 2008.",
    "4-11B": "(arrest continues)",
    "4-12A": "In court, his explanation is still the flea market. He says the Grundig came into his possession in 2007.",
    "4-12B": "Sellers questioned about the market can't recall the sale of the machine. The judges eventually reject his account…",
    "4-13A": "Ursula's brother Michael joins the criminal proceedings… He asks to see the files and reads thousands of pages…",
    "4-13B": "…the detail that he helped Ursula practice piano the day she disappeared. He'd forgotten that moment…",
    "4-14": "In the court's reconstruction, someone records and edits the jingle on the Grundig… copied onto a smaller player… a public phone booth… down the phone line… recorded at the Herrmanns' end.",
    "4-16C": "If you hear a click on the police tape, where did it enter the chain? At the Grundig? At the second machine? In the booth?",
    "4-17A": "The sound on the police tape has passed through every one of those steps…",
    "4-17B": "…He puts his objections in writing to the court.",
    "5-1A": "The judges weigh the tape alongside the rest of the evidence.",
    "5-1B": "They credit details in Pfaffinger's original statement… the binoculars… his debts, his workshop skills… the Grundig in 1981.",
    "5-2C": "In March 2010, after fifty-six days of hearings…",
    "5-2A": "…the court finds Werner Mazurek guilty… and sentences him to life in prison.",
    "5-2B": "His wife, who was tried as an accessory, is acquitted. Mazurek maintains his innocence.",
    "5-3A": "Germany's Federal Court of Justice upholds the conviction.",
    "5-3B": "(continues)",
    "5-4A": "Michael finds another way to put parts of the case back in front of judges. In 2013, he sues Mazurek for twenty thousand euros.",
    "5-4B": "(continues)",
    "5-5A": "Michael has developed tinnitus, a persistent noise in his ear that interferes with teaching music…",
    "5-5B": "…and sleeping. A medical assessment links the condition to the stress of the criminal proceedings.",
    "5-6A": "A retired physicist named Bernd Haider borrows a comparable recorder…",
    "5-6B": "…and spends about a year testing it against the call recordings. He says he can't reproduce the state expert's findings…",
    "5-7A": "The civil court initially awards Michael seven thousand euros…",
    "5-7B": "Michael also submits material… a possible lead involving a boarding school near the woods. In 2019… no grounds to reopen the case.",
    "5-8A": "The award is overturned on appeal in 2020…",
    "5-8B": "…The criminal verdict stands.",
    "5-9A": "In June 2023, after more than fifteen years in custody, Mazurek is released on probation.",
    "5-9B": "He continues to deny involvement.",
    "5-10A": "In 2024, German public broadcasters revisit the case…",
    "5-10B": "…The conviction remains in force.",
    "5-11": "A court has ruled on who took Ursula… Two names. Something her daughter would know. On the other end of the line, nobody answered.",
}
# v2 action notes under the hub's hard rules (nothing moves by itself; a hand or a real event does it; no line rings)
ACTION = {
    "3-1": "Long take: crane down to the path bend, then track along the green wire; the survey flags, the '≈ 140 m' tag and the numbered tents at both lookouts are already in place (aftermath); the camera turns from one lookout's view to the other.",
    "3-2A": "Tape strip on a lightbox with the dusted print already lifted; slow push-in and a focus pull onto the ridges.",
    "3-2B": "Pull back over a field of ≈ 20,000 fingerprint cards; the count painted on the aisle floor.",
    "3-3A": "The tape print and one record card side by side under one lamp; focus pulls from one to the other: no match.",
    "3-3B": "Dusk aerial over the village: the family house and, down the lane, a second house; the camera travels between them.",
    "3-4B": "The workshop counter with the pile of letters as it stood; slow push-in, the lamp falls on the top envelope.",
    "3-5A": "Alibi time-lapse from above: the board, the clock racing 19:30→01:00, players' hands moving pieces in jumps.",
    "3-5B": "Morning: the empty evidence carton, flaps closed, on the workshop floor; an officer's torch beam passes over it.",
    "3-7A": "The offer as a still life under the lamp: banded notes, a small colour TV, a spade leaning at the table.",
    "3-7B": "Soil cross-section on black: the hole as found, a folding rule and a rod laid in it, the box outline inside (as described).",
    "3-8B": "From above: three men walk a loop; flags already mark each spot he named; he stops and points at the next.",
    "3-9A": "The typed statement, already struck through in red, beside the open folder; slow push-in under the lamp.",
    "3-10A": "TV in a dark 1981 living room plays the appeal; pull back through the window: every window in the street flickers the same.",
    "3-10B": "The incident room as tips arrive by phone (v1 shot, kept).",
    "3-11A": "Twelve steel cabinets, stencilled 1–12; the camera tracks the row from 1 to 12.",
    "3-11B": "Push to the tape box; the flip card beside it reads 1989; the tube flickers and dims.",
    "4-1A": "The box on black, slow orbit; numbered markers already stand at the sampling spots.",
    "4-2A": "Screw bag and glass bag on black; a rough red thread pinned between them, as the lab linked them; push-in along it.",
    "4-2B": "Same bench: the thread unpinned and lying slack between the bags; the light on the glass bag dims.",
    "4-4": "Thirty year-blocks on the evidence-room floor 1981→2011; a standing marker at 2007; the last blocks are red; the camera tracks the row.",
    "4-9B": "Three call tapes on black, aluminium bars behind each showing the jingle's envelope; push-in and light falling on the one sunken peak.",
    "4-10A": "Line-up: eleven recorders before a height-line wall, each under its own lamp; the camera tracks the row.",
    "4-10B": "All lamps but one off; slow push-in on the seized machine.",
    "4-12B": "Dawn: an empty flea-market table, a clean rectangle in the dust where a machine stood; no seller.",
    "4-13B": "Late light on the upright piano: the bench with room for two, children's sheet music, the metronome ticking.",
    "4-14": "Long take along one table holding the whole chain (radio → Grundig → cassette → booth model → line → police deck); light falls on each station in turn as the VO names it. Label 'Court reconstruction'.",
    "4-16C": "Same table from above; on each question a light falls on that station (no rings).",
    "5-1B": "Exhibit table under one top light, all items in place: struck statement, binoculars, letters, soldering iron, Grundig; the camera tracks item to item as each is named.",
    "5-2C": "Fifty-six hearing-day folders in a row; a slow track to the last.",
    "5-5B": "Night: a glass of water on the piano, its surface trembling without end; Michael soft behind on the bench.",
    "5-11": "Long take (25 s): from up the dark hall, a slow push to the receiver lying off the hook; the reels slow and stop on 'answered'; hold.",
}
