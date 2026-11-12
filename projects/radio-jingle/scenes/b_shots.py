"""Chat B shot lists (Ch3-5), in film order: (set, move, label). Seconds are estimates (184 wpm) until the
voiceover arrives; the first shot of each chapter carries the title card and 3 s of picture before the voice.
  python b_shots.py            -> prints the lists with estimated seconds
"""
LEAD = 3.0
WORDS = {"ch3": 339, "ch4": 615, "ch5": 405}

CHAPTERS = {
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


def seconds(ch):
    shots = CHAPTERS[ch]
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
