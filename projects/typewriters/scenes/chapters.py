"""Shot order and estimated durations per chapter (seconds at ~125 wpm; replaced by the voiceover timing from
nvidia_doc/edit/align.py when the VO arrives). The intro's first shot carries the 2.5 s lead-in; each chapter's first
shot gives the title ~2 s before the narration.

  python chapters.py            # prints the table and per-chapter totals
"""
# MASTER RULE (Nov 2026): every chapter gets >= 3.0 s of picture under its title card before the voice starts;
# the intro keeps a 2.5 s lead-in. Apply when building the masters after the voiceover arrives.
# DELIVERY: title_card.py (2-line titles, scrim, one PNG per title); textures unpacked into one shared deduped
# folder (<= 2K), identical meshes shared, peak RAM measured on opening the master, zipped into <= 380 MB parts with
# one shared top folder plus a MERGE .bat. FilmCam, packed fonts, 32 samples (make_master).
# CHAPTER-WISE (supersedes one film file): one farm-ready .blend per part: intro (Seldom sting at its end after a
# fade), then one per chapter; each frame range starts at 1, own fades in/out, own audio pair (with / without voice)
# matching exactly; output JPEG quality 92.
LEAD = 2.5

CHAPTERS = {
    "intro": [
        ("twembassy", "street_push", LEAD + 2.6, "1A Moscow. May, 1984."),
        ("twembassy", "crane_up", 3.0, "1B (roof hoist)"),
        ("twambassador", "handover", 2.4, "2A A handwritten note is delivered"),
        ("twambassador", "note", 2.6, "2B ...to the American ambassador."),
        ("twoffice", "typing", 4.6, "3A The NSA has come to replace..."),
        ("twoffice", "notice", 4.8, "3B ...getting an upgrade."),
        ("twembassy", "hoist_rise", 3.8, "4A Over the next several days..."),
        ("twembassy", "roof_swing", 3.8, "4B ...out of the building."),
        ("twattic", "track", 1.6, "5A Copiers. Computers."),
        ("twattic", "staple", 1.6, "5B Encryption machines."),
        ("twembassy", "trailer_seal", 2.4, "6A All of it is going back"),
        ("twembassy", "truck_leave", 2.4, "6B ...to the United States."),
        ("twvault", "push", 6.5, "7A Washington suspects..."),
        ("twvault", "sweep", 7.0, "7B ...machines that send secret messages."),
        ("twoffice", "night_push", 2.0, "8A The one they're looking for"),
        ("twoffice", "night_type", 3.5, "8B ...is a typewriter."),
    ],
    "ch1": [
        ("twlab", "cover", 2.0 + 5.0, "1A CHAPTER 1 THE SWAP / the French show the Americans a bug"),
        ("twlab", "scope", 7.5, "1B ...sends its signal in bursts. An ordinary sweep could miss it..."),
        ("twoffice", "nsa_desk", 5.0, "2A Walter Deeley... helps put together a plan."),
        ("twoffice", "nsa_plans", 9.0, "2B Take the equipment out... keep the embassy working."),
        ("twambassador", "sign", 3.4, "3A President Reagan authorizes the operation"),
        ("twambassador", "folder", 2.4, "3B It's called Project Gunman."),
        ("twoffice", "count", 4.5, "4A No central inventory."),
        ("twinterior", "doors", 4.5, "4B roughly two hundred and fifty typewriters"),
        ("twplant", "line", 4.5, "5A The plant in Lexington can spare fifty."),
        ("twplant", "pallet", 6.0, "5B ...replace the machines in the most sensitive areas."),
        ("twhangar", "wrap", 6.0, "6A staged in Frankfurt... wrapped in burlap"),
        ("twhangar", "seal", 5.0, "6B The staples and seals carry microscopic markings"),
        ("twhangar", "sensor", 3.6, "7A Light sensors record when the doors"),
        ("twhangar", "apron", 2.4, "7B ...of the trailers are opened."),
        ("twambassador", "pocket", 4.8, "8A Hartman gets word... handwritten note"),
        ("twinterior", "chat", 4.0, "8B ...staff hear the embassy is getting an upgrade."),
        ("twinterior", "lift", 2.4, "9A Then the elevator loses power."),
        ("twembassy", "hoist_street", 5.0, "9B The building has a hoist on the roof..."),
        ("twattic", "cable", 3.8, "10A An NSA employee runs wires from alarms"),
        ("twinterior", "marine", 2.6, "10B ...down to the Marines on the sixth floor."),
        ("twinterior", "landing", 4.2, "11A Crews carry the new machines downstairs..."),
        ("twinterior", "stairs", 2.6, "11B Some teletypes barely fit"),
        ("twhangar", "load", 2.6, "12A About eleven tons go back"),
        ("twhangar", "slats", 4.4, "12B ...the typewriter that will give them their first lead."),
    ],
    "ch2": [
        ("twmeade", "team", 2.0 + 4.5, "1A CHAPTER 2 THE X-RAY / Fort Meade, twenty-five people"),
        ("twmeade", "calendar", 2.0, "1B six days a week"),
        ("twmeade", "clear", 2.8, "2A They start with the gear they most expect"),
        ("twmeade", "stack", 2.4, "2B For weeks, they come up empty."),
        ("twmeade", "row", 1.4, "3A Then they turn"),
        ("twmeade", "covers", 1.6, "3B to the typewriters."),
        ("twmeade", "lone", 3.4, "4A On the evening of July twenty-third..."),
        ("twmacro", "coil", 3.0, "4B ...an extra coil in the power switch"),
        ("twmeade", "cabinet", 2.2, "5A He X-rays the whole machine."),
        ("twmeade", "film", 4.4, "5B The film shows a cluster of electronics..."),
        ("twkitchen", "silent", 3.4, "6A Arneson is alone. His wife works for the NSA, too."),
        ("twkitchen", "wide", 4.0, "6B ...can't even tell her what he's found."),
        ("twmeade", "debate", 5.0, "7A The next morning, the engineers debate"),
        ("twmeade", "memory", 5.6, "7B Some typewriters do have electronic memory..."),
        ("twmeade", "pair", 3.4, "8A They take apart two Selectrics side by side"),
        ("twmeade", "barlid", 4.6, "8B ...Inside one of them is a radio transmitter."),
    ],
    "ch3": [
        ("twmacro", "strike", 2.0 + 4.6, "1A CHAPTER 3 THE SIGNAL / the ball tilts and turns"),
        ("twmacro", "platen", 3.6, "1B ...strikes it onto the paper."),
        ("twmacro", "sink", 2.4, "2A Underneath,"),
        ("twmacro", "arms", 2.6, "2B a set of small metal arms controls that movement."),
        ("twmacro", "magnets", 3.0, "3A some of those arms have magnets at their tips."),
        ("twmacro", "xray", 5.6, "3B The hidden electronics can sense which arms move..."),
        ("twembassy", "window_night", 3.2, "4A Once it has enough data,"),
        ("twcity", "antenna", 2.8, "4B ...a short radio burst to a receiver nearby."),
        ("twcity", "tower", 3.4, "5A The designers give those bursts somewhere to hide."),
        ("twkitchen", "family", 3.6, "5B ...the same band as Soviet television broadcasts."),
        ("twkitchen", "post", 2.6, "6A They can also switch the bugs off remotely."),
        ("twmeade", "bars", 3.6, "6B Some draw power... Others carry their own batteries."),
        ("twmeade", "inspect78", 6.6, "7A In 1978, American inspectors had already X-rayed..."),
        ("twmeade", "motorfilm", 7.0, "7B ...The parts could appear perfectly normal."),
        ("twmacro", "space", 5.0, "8A The space bar doesn't move the ball..."),
        ("twoffice", "analyst", 6.0, "8B Soviet analysts work out where the words begin and end."),
    ],
    "ch4": [
        ("twlab", "sixteen", 2.0 + 4.8, "1A CHAPTER 4 WHAT MOSCOW READ / sixteen altered typewriters"),
        ("twlab", "tags", 4.6, "1B thirteen from Moscow, three from Leningrad..."),
        ("twhangar", "customs_torch", 3.4, "2A Soviet intelligence probably got access in transit."),
        ("twhangar", "customs_clock", 3.6, "2B ...left in Soviet customs overnight."),
        ("twoffice", "records_drawer", 4.6, "3A who used the machines... records routinely destroyed"),
        ("twoffice", "records_burn", 4.0, "3B Staff rotated... the trail is incomplete."),
        ("twkitchen", "talk", 3.4, "4A But a former KGB officer"),
        ("twkitchen", "reels", 2.6, "4B gives the NSA one example"),
        ("twoffice", "attache", 3.6, "5A ...in the office of the American agricultural attaché."),
        ("twoffice", "platen", 3.6, "5B Soviet intelligence pulled out the American position on a grain deal"),
        ("twambassador", "talks_wide", 2.4, "6A ...passed it to its negotiators"),
        ("twambassador", "talks_read", 2.0, "6B before the next session."),
        ("twnews", "roll", 2.4, "7A In March 1985, CBS breaks the story."),
        ("twnews", "wire", 2.0, "7B (wire copy)"),
        ("twhangar", "dock_xray", 3.2, "8A The State Department tightens procedures"),
        ("twhangar", "dock_seal", 4.6, "8B The full list... beyond what investigators can reconstruct."),
        ("twvault", "tape", 3.2, "9A The embassy could encrypt a message"),
        ("twvault", "pouch", 3.0, "9B It could send the paper in a sealed pouch."),
        ("twoffice", "page_out", 3.2, "10A By the time the page came out of a bugged machine,"),
        ("twcity", "pullback", 6.0, "10B ...could already have reached a Soviet listening post."),
    ],
}

if __name__ == "__main__":
    for ch, shots in CHAPTERS.items():
        tot = sum(s[2] for s in shots)
        print(f"{ch:6s} {len(shots):2d} shots  {tot:6.1f} s")
