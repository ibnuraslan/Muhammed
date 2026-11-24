"""Scene ambience presets shared by all parts. r_* = looped CC0 recordings, others = synthesised layers.
Every bed is normalised to the same RMS first; the numbers are relative dB (0 = lead layer)."""
_deck = {"r_sea_soft": -3, "sea_calm": -8, "r_wind": -4, "r_creak": -5, "r_rope": -9, "r_flag": -10, "rigging": -13}
LOC = {
    # open sea, exterior
    "sea_low":   {"r_sea": -2, "r_laps": -4, "sea_calm": -7, "r_wind_soft": -6, "r_creak": -14, "flog": -18},
    "sea_wide":  {"r_sea": 0, "sea_calm": -7, "r_wind": -5, "r_flag": -12, "r_creak": -14},
    "sea_far":   {"r_sea_soft": -2, "sea_calm": -5, "r_wind": -5},
    "sea_dg":    {"r_sea": 0, "sea_calm": -7, "r_wind": -4, "r_flag": -12, "r_creak": -12, "rigging": -13},
    "sea_dusk":  {"r_sea": -1, "sea_calm": -6, "r_wind_soft": -5, "bowwash": -11, "r_creak": -14},
    "sea_found": {"r_sea_soft": 0, "sea_calm": -5, "r_wind": -3, "r_flag_hard": -6, "flog": -12},
    "sea_sunset": {"r_sea_soft": -2, "sea_calm": -4, "r_wind_soft": -6, "drone": -16},
    "anchorage": {"r_sea_soft": -3, "r_laps": -3, "r_wind": -6, "r_gulls": -14, "r_creak": -10, "r_rope": -12},
    # decks
    "deck_mc":   dict(_deck),
    "deck_day":  dict(_deck),
    "deck_found": {"r_sea_soft": -4, "r_wind": -4, "r_flag_hard": -7, "r_creak": -7, "r_rope": -10},
    "deck_dusk": {"r_sea_soft": -3, "r_wind_soft": -4, "r_creak": -5, "r_rope": -9, "rigging": -13},
    "dg_deck":   {"r_sea": -3, "r_wind": -3, "r_creak": -6, "r_rope": -8, "r_flag": -8, "rigging": -13},
    "dawn":      {"r_sea_soft": -2, "sea_calm": -5, "r_wind_soft": -4, "gulls_far": -14, "r_creak": -12},
    # weather
    "storm":     {"r_storm": 0, "sea_heavy": -5, "wind_storm": -6, "r_rain_b": -6, "r_creak": -6},
    "night":     {"r_sea_soft": -4, "r_wind": -4, "r_rain": -4, "r_creak": -7, "flame": -18},
    "night_mcu": {"r_storm": -5, "r_rain_b": -5, "r_wind_howl": -6, "r_creak": -6, "flame": -16},
    # harbours
    "quay":      {"r_harbour": 0, "r_laps": -6, "hawser": -9, "r_wind_soft": -10, "r_gulls": -12},
    "harbour":   {"r_harbour": 0, "r_harbour_b": -4, "r_laps": -6, "r_rope": -10, "r_gulls": -10},
    # interiors
    "cabin":     {"r_cabin": 0, "hold": -6, "r_drips": -10, "r_creak": -10},
    "cabin_dry": {"r_cabin_calm": 0, "r_creak": -10, "r_lamp": -24},
    "cabin_pier": {"r_cabin_calm": -2, "r_creak_b": -8, "r_harbour": -12, "r_lamp": -24},
    "galley":    {"r_cabin": -1, "hold": -6, "r_drips": -6, "r_laps": -10},
    "dg_cabin":  {"r_cabin": 0, "r_creak": -10, "r_lamp": -22},
    "hold":      {"hold": 0, "r_creak_b": -6, "r_drips": -14, "r_lamp": -30},
    "hold_ny":   {"hold": -4, "r_harbour": -10, "r_creak_b": -10},
    "cutaway":   {"hold": -2, "r_drone": -6, "drone": -8, "r_creak_b": -12},
    "studio":    {"room": 9, "r_lamp": 2, "r_clock": -5, "r_drone": -6},
    "xray":      {"r_drone": -4, "drone": -8, "room": -8},
    "maquette":  {"room": -2, "r_drone": -8, "r_wind_soft": -14},
    # land
    "parlour":   {"room": 0, "r_clock": -8, "r_fire": -12, "r_wind_soft": -18},
    "school":    {"room": 0, "r_children": -6, "r_clock": -16},
    "court":     {"room": -2, "r_court": 0, "r_murmur": -6, "r_clock": -10},
    "court_quiet": {"room": 7, "r_court": -5, "r_clock": 4, "r_drone": -6},
    "office":    {"room": 0, "r_harbour": -14, "r_clock": -12, "r_lamp": -24},
    "underwater": {"r_underwater": 0, "drone": -12},
}
