"""Design system for the film: palette, type, sizes, easing. One place to change the look."""
import os, math

W, H, FPS = 1920, 1080, 24
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")
SYS = "/usr/share/fonts/opentype/inter/"
MONO_DIR = "/usr/share/fonts/truetype/jetbrains-mono/"

# --- palette (RGB 0-255). Cold graphite world; three signal colours with meaning:
#     CYAN  = compute / data / chips      AMBER = shipments / physical trail      RED = the allegation / restriction
BG = (9, 11, 14)
BG2 = (16, 19, 24)
GRID = (32, 38, 46)
LAND = (22, 27, 33)
BORDER = (52, 61, 72)
STEEL = (138, 151, 168)
TEXT = (232, 236, 241)
DIM = (150, 160, 173)
FAINT = (88, 98, 110)
CYAN = (86, 214, 235)
AMBER = (242, 166, 72)
RED = (232, 72, 77)
PAPER = (236, 232, 223)
INK = (28, 30, 34)

# --- type
F = dict(
    title=os.path.join(FONTS, "InstrumentSerifRegular.ttf"),
    title_i=os.path.join(FONTS, "InstrumentSerifItalic.ttf"),
    quote=os.path.join(FONTS, "SourceSerif4Italic.ttf"),
    serif=os.path.join(FONTS, "SourceSerif4Regular.ttf"),
    serif_b=os.path.join(FONTS, "SourceSerif4SemiBold.ttf"),
    sans=SYS + "Inter-Regular.otf",
    sans_m=SYS + "Inter-Medium.otf",
    sans_sb=SYS + "Inter-SemiBold.otf",
    sans_b=SYS + "Inter-Bold.otf",
    sans_l=SYS + "Inter-Light.otf",
    mono=MONO_DIR + "JetBrainsMono-Regular.ttf",
    mono_m=MONO_DIR + "JetBrainsMono-Medium.ttf",
    mono_b=MONO_DIR + "JetBrainsMono-Bold.ttf",
)

MARGIN = 120          # safe margin (title-safe at 1920)
TRACK_LABEL = 0.22    # letter-spacing for uppercase labels (em)


# --- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(t):     # cubic
    t = clamp(t); return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t); return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_expo(t):
    t = clamp(t); return 1 if t >= 1 else 1 - 2 ** (-10 * t)


def window(t, a, b, fade=0.35):
    """1 within [a, b] seconds, smooth fade-in after a and fade-out before b."""
    return ease_in_out((t - a) / fade) * ease_in_out((b - t) / fade)


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


SMALL = {"a", "an", "and", "the", "of", "to", "in", "on", "for", "at", "by", "or", "if"}


def title_case(s):
    w = s.lower().split()
    return " ".join(x if (i and x in SMALL) else x[:1].upper() + x[1:] for i, x in enumerate(w))
