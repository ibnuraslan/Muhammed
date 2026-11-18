"""Render all blockout frames and assemble STORYBOARD_FULL.pdf."""
import os, re, sys, statistics
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
from shots import SHOTS
from scenes import render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FR = os.path.join(HERE, "frames")
os.makedirs(FR, exist_ok=True)
WPS = 145 / 60.0  # narration rate, words per second
PAUSE = 0.35

text = open(os.path.join(ROOT, "SCRIPT.txt")).read()
SENTS = []
for p in text.strip().split("\n"):
    SENTS += re.split(r"(?<=[.?!])\s+(?=[A-Z])", p.strip())
assert len(SENTS) == 160, len(SENTS)
assert " ".join(SENTS).split() == text.split(), "sentence split must keep the script verbatim"

SEQ = [(0, "COLD OPEN · Aboard the Mary Celeste"), (13, "4 DECEMBER 1872 · The Dei Gratia"), (22, "THE DECK"),
       (32, "THE LOGBOOK AND THE SLATE"), (40, "NEW YORK · November 1872"), (60, "25 NOVEMBER · Santa Maria"),
       (65, "WHAT'S MISSING"), (77, "THE DECISION AND THE PASSAGE"), (90, "GIBRALTAR · The court"),
       (111, "GENOA · The barrels"), (122, "THE PUMP"), (129, "THE DRIFT TEST"), (138, "WHAT WE DON'T KNOW"),
       (146, "LEGEND AND RECORD"), (150, "HOME")]


def sdur(i):
    return len(SENTS[i].split()) / WPS + PAUSE


def rng(s):
    return (s, s) if isinstance(s, int) else s


def timing():
    groups, cur = [], None
    for i, sh in enumerate(SHOTS):
        if sh["s"] is None:
            groups.append([i])
        elif cur is not None and SHOTS[cur[0]]["s"] == sh["s"]:
            cur.append(i)
        else:
            cur = [i]; groups.append(cur)
    covered = []
    for g in groups:
        s = SHOTS[g[0]]["s"]
        if s is None:
            SHOTS[g[0]]["dur_s"] = SHOTS[g[0]]["dur"]
            continue
        a, b = rng(s)
        covered += list(range(a, b + 1))
        total = sum(sdur(k) for k in range(a, b + 1))
        wsum = sum(SHOTS[i]["w"] for i in g)
        for n, i in enumerate(g):
            SHOTS[i]["dur_s"] = total * SHOTS[i]["w"] / wsum
            SHOTS[i]["part"] = (n + 1, len(g))
    assert covered == list(range(160)), "every sentence exactly once, in order"
    t = 0.0
    seq, si = SEQ[0][1], 0
    for n, sh in enumerate(SHOTS):
        sh["id"] = f"{n + 1:03d}"
        sh["tc"] = t
        t += sh["dur_s"]
        if sh["s"] is not None:
            a = rng(sh["s"])[0]
            while si + 1 < len(SEQ) and a >= SEQ[si + 1][0]:
                si += 1
        sh["seq"] = SEQ[si][1]
    return t


def job(n):
    sh = SHOTS[n]
    path = os.path.join(FR, f"shot_{n + 1:03d}.jpg")
    render(sh["sk"], path, label=f"{n + 1:03d}  {sh['size']}", move=sh["mv"], card=sh["card"], tag=sh["tag"],
           silence=sh["silence"], seed=n + 7)
    return path


def tc(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def build_pdf(total):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas as pc
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors

    F = os.path.join(ROOT, "assets", "fonts")
    pdfmetrics.registerFont(TTFont("Courier", os.path.join(F, "CourierPrime-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("CourierB", os.path.join(F, "CourierPrime-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("SansB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    PW, PH = landscape(A4)
    out = os.path.join(ROOT, "STORYBOARD_FULL.pdf")
    c = pc.Canvas(out, pagesize=(PW, PH))
    c.setTitle("The Ship That Came Back Without Its Crew · Storyboard")
    ink = colors.HexColor("#1b1b1b")
    grey = colors.HexColor("#6b6b6b")
    acc = colors.HexColor("#b3541e")
    st = ParagraphStyle("b", fontName="Sans", fontSize=7.6, leading=9.6, textColor=ink)
    stb = ParagraphStyle("bb", parent=st, fontName="SansB")
    scr = ParagraphStyle("s", fontName="Courier", fontSize=8.6, leading=10.4, textColor=ink)
    page = [0]

    def footer():
        page[0] += 1
        c.setFont("Sans", 7)
        c.setFillColor(grey)
        c.drawString(12 * mm, 7 * mm, "THE SHIP THAT CAME BACK WITHOUT ITS CREW · STORYBOARD_FULL · blockout frames, not final renders")
        c.drawRightString(PW - 12 * mm, 7 * mm, f"{page[0]}")

    def table_page(title, rows, widths, sub=None, fs=7.6):
        c.setFillColor(ink)
        c.setFont("SansB", 15)
        c.drawString(12 * mm, PH - 16 * mm, title)
        y0 = PH - 22 * mm
        if sub:
            c.setFont("Sans", 8.5)
            c.setFillColor(grey)
            c.drawString(12 * mm, PH - 21.5 * mm, sub)
            y0 -= 4 * mm
        s1 = ParagraphStyle("t", parent=st, fontSize=fs, leading=fs * 1.25)
        s2 = ParagraphStyle("th", parent=s1, fontName="SansB", textColor=colors.white)
        data = [[Paragraph(str(x), s2) for x in rows[0]]] + [[Paragraph(str(x), s1) for x in r] for r in rows[1:]]
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ink), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1efea")]),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcac0")),
                               ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]))
        avail = y0 - 14 * mm
        parts = t.split(PW - 24 * mm, avail)
        first = True
        for p in parts:
            if not first:
                c.showPage()
                c.setFillColor(ink); c.setFont("SansB", 15)
                c.drawString(12 * mm, PH - 16 * mm, title + " (cont.)")
                y0 = PH - 22 * mm
            w_, h_ = p.wrap(PW - 24 * mm, avail)
            p.drawOn(c, 12 * mm, y0 - h_)
            footer()
            first = False
        c.showPage()

    durs = [s["dur_s"] for s in SHOTS]
    vo_words = sum(len(s.split()) for s in SENTS)
    nsil = sum(1 for s in SHOTS if s["silence"])
    # ---------- cover ----------
    c.setFillColor(colors.HexColor("#14181b"))
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    from reportlab.lib.utils import ImageReader
    ih = PH * 0.70; iw = ih * 16 / 9
    c.drawImage(ImageReader(os.path.join(FR, "shot_001.jpg")), (PW - iw) / 2, PH * 0.30, iw, ih)
    c.setFillColor(colors.HexColor("#14181b"))
    c.rect(0, 0, PW, PH * 0.34, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("CourierB", 26)
    c.drawString(14 * mm, PH * 0.34 - 16 * mm, "THE SHIP THAT CAME BACK WITHOUT ITS CREW")
    c.setFont("Courier", 13)
    c.drawString(14 * mm, PH * 0.34 - 25 * mm, "Seldom · The Mary Celeste · Full shot-by-shot storyboard (for approval)")
    c.setFont("Sans", 9)
    c.setFillColor(colors.HexColor("#c9cfd2"))
    lines = [f"{len(SHOTS)} shots · runtime ≈ {tc(total)} ({vo_words} VO words at 145 wpm + {nsil} silence beats)",
             f"Median shot {statistics.median(durs):.1f} s · mean {statistics.mean(durs):.1f} s · longest {max(durs):.1f} s",
             "Format: 16:9 · final render 2560×1440 (2K) · 24 fps · Courier Prime burned-in captions",
             "Frames in this PDF are blockout sketches (grey 3D massing + lighting tone) to plan camera, staging and light. No final renders."]
    for i, l in enumerate(lines):
        c.drawString(14 * mm, PH * 0.34 - 36 * mm - i * 5.2 * mm, l)
    c.showPage()

    # ---------- look page (approve first) ----------
    from lookdev import FRAMES as LOOK
    c.setFillColor(ink); c.setFont("SansB", 15)
    c.drawString(12 * mm, PH - 16 * mm, "0 · THE LOOK (approve first)")
    c.setFont("Sans", 8.5); c.setFillColor(grey)
    c.drawString(12 * mm, PH - 21.5 * mm, "Light and grade tests on blockout geometry. Photoreal materials and characters come at render (needs Blender, blocked here for now).")
    lw = (PW - 24 * mm - 2 * 5 * mm) / 3
    lh = lw * 9 / 16
    for i, (name, _, cap) in enumerate(LOOK):
        x = 12 * mm + i * (lw + 5 * mm)
        c.drawImage(ImageReader(os.path.join(FR, name)), x, PH - 27 * mm - lh, lw, lh)
        p = Paragraph(f"<b>Style frame {i + 1}.</b> {cap}", st)
        _, ph_ = p.wrap(lw, 30 * mm)
        p.drawOn(c, x, PH - 29 * mm - lh - ph_)
    pal = [("Atlantic, 4 Dec (noon)", ["#101619", "#3b474d", "#6e7c82", "#b9c3c6", "#e2e8e9"], "Cold silver overcast, soft top light, haze on the horizon. Wet wood goes near-black; canvas glows when backlit"),
           ("Below decks", ["#07090b", "#1d252a", "#4e5b61", "#a9b7bb", "#f0f2f0"], "One hard skylight or port shaft, dust in the beam, fill under 1/8; brass and water catch specular highlights"),
           ("New York / cabin lamp", ["#140c07", "#4a2f1a", "#8a5a33", "#d6a873", "#fbe5bd"], "Warm oil lamp + autumn window; ochre and walnut; soft haze over the pier"),
           ("Santa Maria dawn", ["#1c0f0d", "#5c3524", "#a96f4b", "#f0b884", "#fff0d2"], "Low gold sun through sea haze; ship in silhouette; island softened by distance"),
           ("Gale", ["#03060c", "#172433", "#3a4f66", "#8aa3b8", "#d7e6f0"], "Blue-black; lightning rim on sails; the lantern is the only warm light; rain, spray, motion blur"),
           ("Gibraltar court / Genoa", ["#130d09", "#3e2a1c", "#7a5638", "#cfa577", "#f6e5c8"], "Warm window light and dust in the courtroom; Genoa in warm daylight"),
           ("Reconstruction / legend", ["#1c1c1e", "#4a4a4c", "#7c7c7e", "#b0b0b0", "#d8d8d8"], "Speculative beats desaturated; the warm-meal legend in sepia, then a match-cut to cold truth")]
    y = PH - 29 * mm - lh - 16 * mm
    c.setFillColor(ink); c.setFont("SansB", 10)
    c.drawString(12 * mm, y, "Colour script by location")
    y -= 5 * mm
    for name, sw, note in pal:
        c.setFillColor(ink); c.setFont("SansB", 8)
        c.drawString(12 * mm, y - 3.2 * mm, name)
        for k, hx in enumerate(sw):
            c.setFillColor(colors.HexColor(hx))
            c.rect(62 * mm + k * 9 * mm, y - 4.5 * mm, 8.5 * mm, 5 * mm, fill=1, stroke=0)
        c.setFillColor(ink); c.setFont("Sans", 7.6)
        c.drawString(110 * mm, y - 3.2 * mm, note)
        y -= 6.4 * mm
    footer(); c.showPage()

    # ---------- how to read ----------
    table_page("1 · How to read this board", [
        ["Item", "Meaning"],
        ["Frame", "Blockout sketch: grey 3D massing, a single key light and the time-of-day tone. Yellow arrows = camera move. Top-left = shot number and size/lens. Red SILENCE tag = no VO, ambience only."],
        ["Script", "The VO sentence that plays over the shot, verbatim from the approved script (Courier). When one sentence spans several shots it is marked 'part n/m'. Script text has not been changed."],
        ["Timecode", f"Estimated from the script at 145 words/min + {PAUSE}s between sentences, plus the silence beats. Final timing follows the user's voiceover."],
        ["Cards", "Blue arrow box on the frame = a card SLIDES in (never fades). Person cards right, place cards left: B&W photo with white border, typewriter name and role."],
        ["Reconstruction", "Speculative beats (what may have happened) are desaturated and labelled, faces turned away, so they never read as record."],
        ["Grade per location", "Atlantic: cold silver overcast · New York: warm autumn haze, warm lamp cabins · Santa Maria: dawn gold · Gale: blue-black storm · Gibraltar: clear winter light, warm court · Genoa: warm daylight · Explainers: white maquette · Present day: cool modern · Legend: sepia · Home: snow light"],
    ], [40, 233])

    table_page("2 · Hard rules applied to every shot", [
        ["Rule", "How the board handles it"],
        ["Nothing moves by itself", "Every moving thing has a cause in frame: wind moves sails/ropes/pennants (shown by gusts on the water), the roll moves coats and the boom, people move every prop. The unmanned wheel stays still. Maquette pencil lines are drawn by a hand with its person in frame."],
        ["No hand without its person", "All inserts are over-the-shoulder: head + shoulder + arm in frame (soft foreground), hand sharp on the prop. No floating hands."],
        ["Marks physically real", "Chalk on the slate and tally board, ink in the logbook, cut notches and a wet line on the sounding rod, pencil on the chart, stains soaked into the deck grain, chalk on the empty barrels."],
        ["No cheap evidence props", "Period-accurate, worn objects only: binnacle compass, gimballed chronometer box, sextant case, reed organ, period dolls, consular wax seal."],
        ["Every action has meaning", "Each shot has one verb tied to the script line (presses, lifts, measures, chalks, nails, kneels)."],
        ["No clipping", "Staging keeps bodies apart; props held by one hand; collision QA pass planned at render."],
        ["Natural walks and faces", "Walks ≤ 2 s, from behind, in low light or top-down. Small held expressions; no lip-sync (speakers seen from behind or OTS)."],
        ["Ripples", "Only as soft FILLED orange bands (Santa Maria pin, the found position). Never line rings."],
        ["No flat 2D graphics", "Maps are a physical sea-relief maquette on a table; explainers are white 3D maquettes and cutaways."],
        ["Chapter titles", "None planned (per brief). If added: uniform 52% dim, no oval, 2–3 s silence, VO after."],
        ["Sound", f"SFX on every action, constant ambience, {nsil} silence beats before reveals (no one, the boat, 3½ ft, no blood, nine barrels, 'It could.', the dolls, the last line)."],
        ["Captions & photos", "Burned-in Courier Prime captions via caption_burnin.py. Cards via callout.py (branch claude/killer-in-house). Free-licence photos only, listed in CREDITS.txt."],
    ], [48, 225])

    # ---------- cast and cards ----------
    table_page("3 · Cast, cards and photo sources (to confirm)", [
        ["Who", "Role in film", "Look (blockout)", "Card", "Free-licence photo"],
        ["Oliver Deveau", "First mate, Dei Gratia; our eyes", "Late 30s, peaked cap, beard, wool coat", "Right · shot 003", "Period portrait (public domain) to verify"],
        ["David Morehouse", "Captain, Dei Gratia", "Peaked cap, beard", "Right · shot 029", "Period portrait (public domain) to verify"],
        ["Benjamin Briggs", "Captain, Mary Celeste", "Beard, no cap indoors", "Right · NY sequence", "Portrait (public domain, Wikimedia)"],
        ["Sarah Briggs", "Captain's wife", "Hair in a bun, dark dress", "Right · NY sequence", "Portrait (public domain, Wikimedia)"],
        ["Sophia Briggs (2)", "Daughter aboard", "Small child", "No card", "—"],
        ["Arthur Briggs (7)", "Son, stays in Massachusetts", "Boy, school clothes", "No card", "—"],
        ["Helmsman, sailors, pilot, visitor, stevedores, clerk", "Supporting", "Faces small or turned away", "No card", "—"],
        ["Frederick Solly Flood", "Attorney General, Gibraltar", "Barrister's wig and robe in court", "Right · court", "Need a free photo; else no photo card (ask)"],
        ["Diver, surveyor, chemist, judge, consular clerk", "Inquiry", "Period clothes", "No card", "—"],
        ["Anne MacGregor", "Documentary researcher", "Present day", "Right · pump", "Likely no free photo: name-only card or skip (ask)"],
        ["Phil Richardson", "Oceanographer", "Present day", "Right · drift test", "Likely no free photo: name-only card or skip (ask)"],
        ["Places", "New York (Pier 50), Staten Island, Santa Maria, Gibraltar, Genoa, Marion (Mass.)", "", "Left", "19th-c. public-domain photos / CC0 photos"],
        ["Vessels", "Dei Gratia, Mary Celeste", "", "Left (as place cards)", "1861 painting of the ship as Amazon (PD); Dei Gratia to find"],
    ], [42, 52, 50, 34, 95])

    # ---------- sequence overview ----------
    rows = [["Sequence", "Shots", "Starts", "Length", "Script sentences", "Hero / signature moment"]]
    hero = {0: "One-take crane up the hull (002); push into the child-sized hollow (008)",
            1: "Sail sighted through haze (015); 'Nobody answers' silence (035)",
            2: "X-ray maquette: the rod finds 3½ ft (048)", 3: "Slate → match-cut into the relief maquette, orange band at Santa Maria",
            4: "Barrels into the hold; the bonnet bump; the pilot takes the last letter", 5: "Dawn landfall; the last chalk stroke",
            6: "White-maquette roll-call of what's missing", 7: "Night gale near the Strait; the Rock lost in rain",
            8: "Diver under the hull; the clear test tube", 9: "Red oak vs white oak macro", 10: "Coal dust in the valve (macro)",
            11: "Pencil drift line meets the second pin: 'It could.'", 12: "The towing line and the ship sailing away (reconstruction)",
            13: "Legend warm table → match-cut to the soaked real table", 14: "Broken-armed doll; the empty sea"}
    for k, (a, name) in enumerate(SEQ):
        ids = [s for s in SHOTS if s["seq"] == name]
        b = SEQ[k + 1][0] - 1 if k + 1 < len(SEQ) else 159
        rows.append([name, f"{ids[0]['id']}–{ids[-1]['id']} ({len(ids)})", tc(ids[0]["tc"]), f"{sum(s['dur_s'] for s in ids):.0f} s",
                     f"{a + 1}–{b + 1}", hero[k]])
    table_page("4 · Sequence overview (no chapter titles)", rows, [55, 28, 16, 16, 24, 134],
               sub=f"Total ≈ {tc(total)} · {len(SHOTS)} shots · median {statistics.median(durs):.1f} s")

    table_page("5 · Sound design plan (Atrium-style)", [
        ["Layer", "Plan"],
        ["Ambience beds (never true silence)", "Open Atlantic: wind + swell + rigging creak + canvas flog · below decks: hull groan, drips, muffled sea · New York pier: gulls, carts on cobbles, stevedores, harbour bell · storm: gale, rain, thunder, timbers · Gibraltar: harbour bells, gulls; court room tone + clock · underwater: pressure, air-pump hiss · Genoa: quay bells and barrels · present day: quiet room tone · Massachusetts: clock tick, snow wind"],
        ["Foley", "One sound per action in every shot (listed per shot): boots on wet planks, ladder, blanket squelch, rod line, chalk, pen nib, latch, sword rasp, hammer on the notice, wax seal, straw"],
        ["Silence before reveals", f"{nsil} beats of 1–2.5 s with music out and ambience only (marked red on the frames)"],
        ["Music", "Low strings/pulse bed; first cue as the three men sail her away (020); swells at Gibraltar exit and the final push; drops out before each reveal"],
        ["Mix", "−14 LUFS integrated, LRA 3–5 LU, VO on top (user supplies VO later); music ducked 6–8 dB under VO"],
    ], [55, 218])

    # ---------- shot pages ----------
    from reportlab.lib.utils import ImageReader
    per = 3
    fw = 104 * mm
    fh = fw * 9 / 16
    rowh = (PH - 26 * mm) / per
    for i0 in range(0, len(SHOTS), per):
        c.setFillColor(ink)
        c.setFont("SansB", 9)
        c.drawString(12 * mm, PH - 11 * mm, SHOTS[i0]["seq"])
        for k, sh in enumerate(SHOTS[i0:i0 + per]):
            top = PH - 15 * mm - k * rowh
            c.drawImage(ImageReader(os.path.join(FR, f"shot_{sh['id']}.jpg")), 12 * mm, top - fh, fw, fh)
            x = 12 * mm + fw + 6 * mm
            wcol = PW - x - 12 * mm
            c.setFillColor(acc if sh["silence"] else ink)
            c.setFont("SansB", 10.5)
            head = f"SHOT {sh['id']}   {tc(sh['tc'])}   {sh['dur_s']:.1f} s   {sh['size']}"
            c.drawString(x, top - 4 * mm, head)
            if sh["s"] is None:
                script = "<i>(no narration)</i>"
            else:
                a, b = rng(sh["s"])
                txt = " ".join(SENTS[a:b + 1])
                pt = f"  <font color='#6b6b6b'>[part {sh['part'][0]}/{sh['part'][1]}]</font>" if sh["part"][1] > 1 else ""
                script = f"“{txt}”{pt}"
            items = [("Script", Paragraph(script, scr)), ("Camera", Paragraph(sh["camera"], st)),
                     ("Characters / action", Paragraph(sh["action"], st)), ("Light / time", Paragraph(sh["light"], st)),
                     ("SFX", Paragraph(sh["sfx"], st))]
            extra = []
            if sh["card"]:
                extra.append(f"{'Person' if sh['card'][0] == 'r' else 'Place'} card slides in ({'right' if sh['card'][0] == 'r' else 'left'}): {sh['card'][1]} · {sh['card'][2]}")
            if sh["tag"]:
                extra.append(f"Date/place tag (typewriter, top centre): {sh['tag']}")
            if sh["note"]:
                extra.append(sh["note"])
            if extra:
                items.append(("Notes", Paragraph(" · ".join(extra), st)))
            data = [[Paragraph(f"<b>{a}</b>", ParagraphStyle('l', parent=st, textColor=grey)), b] for a, b in items]
            t = Table(data, colWidths=[27 * mm, wcol - 27 * mm])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.2),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            w_, h_ = t.wrap(wcol, rowh - 8 * mm)
            t.drawOn(c, x, top - 6.5 * mm - h_)
            c.setStrokeColor(colors.HexColor("#d6d1c7"))
            c.setLineWidth(0.4)
            if k < per - 1:
                c.line(12 * mm, top - rowh + 2.5 * mm, PW - 12 * mm, top - rowh + 2.5 * mm)
        footer()
        c.showPage()
    c.save()
    return out


if __name__ == "__main__":
    total = timing()
    if "--no-render" not in sys.argv:
        with Pool(4) as p:
            p.map(job, range(len(SHOTS)))
    out = build_pdf(total)
    d = [s["dur_s"] for s in SHOTS]
    print(out, len(SHOTS), "shots", f"{total:.0f}s", f"median {statistics.median(d):.2f}", f"max {max(d):.1f}")
