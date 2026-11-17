"""Per-frame format: chapter titles (fmt_layers) + the shared callout module's cards and captions."""
import sys, os, numpy as np
from PIL import Image
SP = '/tmp/claude-0/-home-user-Muhammed/8eef100b-02db-57dc-974f-d5b225739e26/scratchpad'
sys.path.insert(0, SP + '/fmt/mod/scenes'); sys.path.insert(0, SP + '/scripts')
import callout, caption_burnin
import fmt_layers as L
from fmt_cards import CARDS, P, END, HOLD
CUES = caption_burnin.parse_srt(SP + '/srt/nvidia_part1.srt')
_skip = set()
def photo_ok(key):
    try: return open(P + key + '.jpg', 'rb').read(3) == b'\xff\xd8\xff'
    except OSError: return False
def fmt(img, n, log=print):
    t = (n - 1) / 24
    f = L.apply_title(img.astype(np.float32), n)
    im = Image.fromarray(np.clip(f + 0.5, 0, 255).astype(np.uint8))
    for t0, key, name, role, side, crop in CARDS:
        dur = min(0.35 + HOLD + 0.3, END - t0)
        if not (t0 <= t < t0 + dur): continue
        if not photo_ok(key):
            if key not in _skip: _skip.add(key); log(f'CARD SKIPPED (no photo): {key}')
            continue
        fn = callout.person_right if side == 'right' else callout.place_left
        im = fn(im, P + key + '.jpg', name, role, crop=crop, slide=callout.card_slide(t - t0, dur))
    for a, z, text in CUES:
        if a <= t < z: im = callout.caption(im, text); break
    return np.asarray(im)
