"""Part A running order (Cold Open, Chapter One, Chapter Two): (set, move) per shot, in script order.
Durations: until the voiceovers arrive, each shot's seconds are its DUR scaled so a chapter fills its estimate
(184 wpm + lead). Chapter B's lists are added from its branch (CH3..CH5) for the film assembly."""
COLD = [("house", m) for m in ("co_push", "co_profile", "co_officer", "co_tape", "co_top", "co_meter", "co_brother", "co_brother_side")]
CH1 = [("house", "p_title"), ("house", "p_page"), ("village", "gate"), ("village", "lane"), ("path", "ride_track"), ("path", "ride_reeds"),
       ("house", "dial"), ("house", "hangup"), ("path", "bend_push"), ("path", "bend_high"), ("path", "father_walk"), ("path", "uncle_torch"),
       ("path", "meet_wide"), ("path", "father_call"), ("path", "night_line"), ("path", "night_fire"), ("path", "dog_low"), ("path", "dog_front"),
       ("path", "brush_find"), ("path", "brush_ring"), ("path", "bro_run"), ("path", "bro_line"), ("house", "bench"), ("house", "pwin"),
       ("path", "heli"), ("path", "divers"), ("house", "k_radio"), ("house", "k_window"), ("house", "ring"), ("house", "listen"),
       ("village", "post_ride"), ("village", "post_box"), ("house", "letter"), ("house", "read"), ("house", "thread"), ("house", "door"),
       ("house", "call_left"), ("house", "toys"), ("house", "suitcase"), ("house", "latch"), ("village", "fiat_load"), ("village", "fiat_wide"),
       ("house", "silent"), ("house", "stairs")]
CH2 = [("woods", m) for m in ("line", "tape", "rods", "rods_dog", "hit", "converge", "dig", "sweep", "lid", "bolt", "lift", "cap")] + \
      [("box", m) for m in ("crane", "cable", "shelf", "radio", "pipe", "smoke", "experts", "door")] + \
      [("house", "co2_back"), ("house", "co2_toy")] + [("woods", m) for m in ("spr_orbit", "spr_low", "torch_far", "dark", "pull")] + [("path", "bend_long")]
TARGET = {"cold": 29.3, "ch1": 174.1, "ch2": 123.6}          # narration seconds (184 wpm)
LEAD = {"cold": 2.5, "ch1": 3.0, "ch2": 3.0}                    # picture before the first word (on the first shot)
PARTS = {"cold": COLD, "ch1": CH1, "ch2": CH2}


def durations(part):
    import importlib
    shots = PARTS[part]
    base = [importlib.import_module("sc_" + s).DUR[m] for s, m in shots]
    k = TARGET[part] / sum(base)
    return [(s, m, round(max(3.0, b * k) + (LEAD[part] if i == 0 else 0.0), 2)) for i, ((s, m), b) in enumerate(zip(shots, base))]


if __name__ == "__main__":
    import sys
    for part in PARTS:
        d = durations(part)
        print(part, len(d), "shots", round(sum(x[2] for x in d), 1), "s")
