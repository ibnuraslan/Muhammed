"""Paper textures for the evidence documents (diegetic print, generic wording, no real names or brands):
thermal till receipts, a typed lease/inventory form, a typed letter (torn into scraps on the lightbox), and the folded
diamond paper ("briefke"). Writes PNGs to assets_gen/docs/.   python3 tools/gen_docs.py"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets_gen", "docs")
os.makedirs(D, exist_ok=True)
FD = "/usr/share/fonts/truetype"
MONO = os.path.join(FD, "dejavu", "DejaVuSansMono.ttf")
MONOB = os.path.join(FD, "dejavu", "DejaVuSansMono-Bold.ttf")
SERIF = os.path.join(FD, "liberation", "LiberationSerif-Regular.ttf")
SERIFB = os.path.join(FD, "liberation", "LiberationSerif-Bold.ttf")
COUR = os.path.join(FD, "liberation", "LiberationMono-Regular.ttf")
F = lambda p, s: ImageFont.truetype(p if os.path.exists(p) else MONO, s)


def paper(w, h, base, rng, fibre=6):
    im = Image.new("RGB", (w, h), base)
    nz = Image.effect_noise((w // 3, h // 3), 40).resize((w, h), Image.BICUBIC).convert("RGB")
    return Image.blend(im, nz, 0.006 * fibre)


def fade(im, rng, n=5, strength=60):
    """Thermal print fades unevenly: lighten a few soft patches."""
    w, h = im.size
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h); r = rng.randrange(w // 4, w)
        d.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=rng.randrange(strength // 2, strength))
    m = m.filter(ImageFilter.GaussianBlur(w // 8))
    return Image.composite(Image.new("RGB", (w, h), (245, 244, 238)), im, m)


def receipt(seed):
    rng = random.Random(seed)
    W, H = 600, 1900
    im = paper(W, H, (246, 245, 240), rng, 4); d = ImageDraw.Draw(im)
    ink = (52, 52, 58); f = F(MONO, 26); fb = F(MONOB, 34); y = 60
    def c(t, font=f, dy=40):
        nonlocal y
        tw = d.textlength(t, font=font); d.text(((W - tw) / 2, y), t, font=font, fill=ink); y += dy
    def row(a, b, dy=36):
        nonlocal y
        d.text((40, y), a, font=f, fill=ink); tw = d.textlength(b, font=f); d.text((W - 40 - tw, y), b, font=f, fill=ink); y += dy
    c("SUPERMARKT", fb, 48); c("Filiaal 214 - Antwerpen"); c("Tel. 03 000 00 00"); c("BTW BE 0000.000.000", dy=56)
    c("-" * 34, dy=40)
    items = [("STOKBROOD WIT", "1,15"), ("SALAMI GESNEDEN 150G", "2,49"), ("MINERAALWATER 1,5L", "0,69"),
             ("CHIPS PAPRIKA", "1,29"), ("KOFFIE FILTER 250G", "2,95"), ("BOTER 250G", "1,39"), ("APPELS 1KG", "1,79"),
             ("CHOCOLADE MELK", "0,99"), ("YOGHURT NATUUR", "0,85"), ("SIGARETTEN", "4,20"), ("TOILETPAPIER 8R", "3,49"),
             ("KAAS JONG 300G", "3,15"), ("COLA 1,5L", "1,05")]
    rng.shuffle(items); tot = 0.0
    for a, b in items[:rng.randrange(7, 11)]:
        row(a, b); tot += float(b.replace(",", "."))
    c("-" * 34, dy=40)
    d.text((40, y), "TOTAAL EUR", font=fb, fill=ink); t = f"{tot:.2f}".replace(".", ","); d.text((W - 40 - d.textlength(t, font=fb), y), t, font=fb, fill=ink); y += 56
    row("CONTANT", f"{tot + rng.choice((0.5, 1.2, 5.0)):.2f}".replace(".", ",")); row("TERUG", "")
    y += 20; c("-" * 34, dy=40)
    row("BTW 6%", f"{tot * 0.057:.2f}".replace(".", ","))
    y += 30; c(f"{rng.randrange(10, 17)}/02/2003   {rng.randrange(9, 20)}:{rng.randrange(10, 59)}")
    c(f"KASSA 03   BON {rng.randrange(1000, 9999)}   KASSIER 12", dy=60)
    c("BEDANKT EN TOT ZIENS", dy=50)
    # print head streaks + fading
    for _ in range(3):
        x = rng.randrange(W); d.line((x, 0, x, H), fill=(235, 234, 230), width=2)
    im = fade(im.crop((0, 0, W, y + 80)), rng, 6, 70).filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(D, f"receipt_{seed}.jpg"), quality=88)


def form(seed):
    rng = random.Random(seed)
    W, H = 1240, 1754
    im = paper(W, H, (240, 238, 230), rng, 5); d = ImageDraw.Draw(im)
    ink = (30, 30, 38); fh = F(SERIFB, 46); f = F(SERIF, 28); fm = F(COUR, 27)
    d.text((110, 110), "HUUROVEREENKOMST - KANTOORRUIMTE", font=fh, fill=ink)
    d.text((110, 175), "Office lease agreement  ·  ref. " + f"{rng.randrange(100, 999)}/{rng.randrange(10, 99)}-B", font=f, fill=ink)
    d.line((110, 225, W - 110, 225), fill=ink, width=3)
    y = 270
    for lab, val in (("Verhuurder / Lessor", "Beheersmaatschappij  N.V."), ("Huurder / Tenant", "(firma)  B.V.B.A."),
                     ("Ruimte / Unit", f"Verdieping {rng.randrange(2, 9)}  -  lokaal {rng.randrange(10, 60)}"),
                     ("Ingangsdatum / Start", "01 / 07 / 2000"), ("Duur / Term", "3 jaar / years"),
                     ("Huurprijs / Rent", f"EUR {rng.randrange(600, 1400)},00 per maand"),
                     ("Sleutels / Keys", "2 x deur, 1 x badge kluisgang"), ("Waarborg / Deposit", "3 maanden")):
        d.text((110, y), lab, font=f, fill=ink); d.text((560, y), val, font=fm, fill=(25, 35, 80))
        d.line((550, y + 38, W - 110, y + 38), fill=(120, 120, 120), width=1); y += 62
    y += 30
    words = ("de huurder verbindt zich ertoe het goed als een goede huisvader te gebruiken en het in de staat terug te "
             "geven waarin hij het ontvangen heeft behoudens normale slijtage de toegang tot de gemeenschappelijke "
             "delen gebeurt met de badge die bij ondertekening wordt overhandigd").split()
    for k in range(14):
        rng.shuffle(words); line = " ".join(words[:11]).capitalize() + "."
        d.text((110, y), f"{k + 1}.  " + line[:78], font=f, fill=ink); y += 44
    y += 60
    for x0 in (110, 700):
        d.line((x0, y + 70, x0 + 420, y + 70), fill=ink, width=2); d.text((x0, y + 80), "Handtekening / Signature", font=f, fill=ink)
        pts = [(x0 + 30 + i * 18, y + 50 + rng.randrange(-22, 22)) for i in range(18)]
        d.line(pts, fill=(20, 30, 90), width=3)
    # stamp
    sx, sy = 880, 120
    d.ellipse((sx, sy, sx + 220, sy + 220), outline=(150, 40, 50), width=6); d.text((sx + 40, sy + 92), "ONTVANGEN", font=F(SERIFB, 30), fill=(150, 40, 50))
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    im.save(os.path.join(D, f"form_{seed}.jpg"), quality=88)


def letter(seed):
    """Typed page: a list of addresses and figures (what the torn scraps came from) - generic, no names."""
    rng = random.Random(seed)
    W, H = 1240, 1754
    im = paper(W, H, (238, 236, 228), rng, 6); d = ImageDraw.Draw(im)
    ink = (28, 28, 34); f = F(COUR, 30)
    y = 140
    d.text((120, y), f"Overzicht  {rng.randrange(1, 28)}.{rng.randrange(1, 12)}.02", font=F(COUR, 36), fill=ink); y += 90
    streets = ("Pelikaanstraat", "Hoveniersstraat", "Schupstraat", "Rijfstraat", "Lange Herentals", "Vestingstraat")
    for k in range(26):
        if k % 6 == 5:
            y += 30; continue
        t = f"{rng.choice(streets):<18} {rng.randrange(1, 90):>3}   box {rng.randrange(1, 160):>3}   {rng.randrange(10, 99)},{rng.randrange(0, 99):02d} ct"
        d.text((120, y), t, font=f, fill=ink); y += 46
    y += 40
    for k in range(8):
        d.text((120, y), "".join(rng.choice("0123456789  -/") for _ in range(46)), font=f, fill=ink); y += 46
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(D, f"letter_{seed}.jpg"), quality=88)


def briefke(seed):
    """Diamond paper: white wrap with a blue printed border and a pencilled carat weight."""
    rng = random.Random(seed)
    W, H = 1200, 820
    im = paper(W, H, (246, 246, 244), rng, 3); d = ImageDraw.Draw(im)
    blue = (40, 70, 140)
    d.rectangle((30, 30, W - 30, H - 30), outline=blue, width=4); d.rectangle((44, 44, W - 44, H - 44), outline=blue, width=1)
    d.text((80, 70), "CTS ........", font=F(SERIF, 40), fill=blue); d.text((80, 130), "Nr ........", font=F(SERIF, 40), fill=blue)
    d.text((300, 62), f"{rng.randrange(1, 9)},{rng.randrange(10, 99)}", font=F(SERIFB, 52), fill=(70, 70, 75))
    d.text((300, 122), f"{rng.randrange(100, 999)}", font=F(SERIFB, 52), fill=(70, 70, 75))
    # fold lines (printed paper is folded in thirds both ways)
    for x in (W // 3, 2 * W // 3):
        d.line((x, 0, x, H), fill=(225, 225, 222), width=3)
    for y in (H // 3, 2 * H // 3):
        d.line((0, y, W, y), fill=(225, 225, 222), width=3)
    im.save(os.path.join(D, f"briefke_{seed}.jpg"), quality=88)


def faxcover(seed):
    """Telefax cover sheet, Antwerp federal judicial police -> Turin police headquarters (institutions only)."""
    rng = random.Random(seed)
    W, H = 1240, 1754
    im = paper(W, H, (242, 241, 236), rng, 4); d = ImageDraw.Draw(im)
    ink = (22, 22, 28)
    d.rectangle((90, 90, W - 90, 300), outline=ink, width=5)
    d.text((130, 120), "TELEFAX", font=F(SERIFB, 120), fill=ink)
    d.text((780, 150), "DRINGEND", font=F(SERIFB, 54), fill=(150, 30, 35)); d.text((780, 215), "URGENTE", font=F(SERIFB, 54), fill=(150, 30, 35))
    y = 360
    for lab, val in (("Aan / A / To", "QUESTURA DI TORINO - Squadra Mobile"), ("Fax", "0039 011 558 ...."),
                     ("Van / Da / From", "Federale Gerechtelijke Politie - Antwerpen"), ("Datum", "19.02.2003   11:42"),
                     ("Betreft / Oggetto", "Verzoek identificatie - richiesta di identificazione"), ("Pagina's / Pagine", "4 (incl. deze)")):
        d.text((110, y), lab, font=F(SERIF, 34), fill=ink); d.text((470, y), val, font=F(COUR, 32), fill=ink)
        d.line((460, y + 44, W - 110, y + 44), fill=(120, 120, 120), width=1); y += 74
    y += 40
    body = ("In het kader van het onderzoek naar de inbraak in de kluis van het diamantcentrum verzoeken wij u om "
            "inlichtingen over de huurder van een kantoor in het gebouw, afkomstig uit Turijn. Bijgevoegd: kopie "
            "huurovereenkomst, kopie identiteitsdocument, vingerafdrukken. Graag spoedig antwoord.").split()
    line = ""
    for wd in body:
        if d.textlength(line + " " + wd, font=F(SERIF, 32)) > W - 240:
            d.text((110, y), line.strip(), font=F(SERIF, 32), fill=ink); y += 46; line = ""
        line += " " + wd
    d.text((110, y), line.strip(), font=F(SERIF, 32), fill=ink); y += 120
    d.line((110, y + 60, 560, y + 60), fill=ink, width=2); d.text((110, y + 70), "Handtekening", font=F(SERIF, 28), fill=ink)
    d.line([(140 + i * 22, y + 40 + rng.randrange(-18, 18)) for i in range(16)], fill=(20, 30, 90), width=3)
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    im.save(os.path.join(D, f"faxcover_{seed}.jpg"), quality=88)


def lcd():
    im = Image.new("RGB", (640, 120), (60, 78, 40)); d = ImageDraw.Draw(im)
    f = F(MONOB, 44)
    d.text((18, 8), "TX  TORINO", font=f, fill=(12, 18, 8)); d.text((18, 62), "0039011558..  P01", font=f, fill=(12, 18, 8))
    im.save(os.path.join(D, "fax_lcd.jpg"), quality=92)


def cards():
    """Index cards for the investigation board (labels in Dutch, place names only)."""
    for k, (t1, t2) in enumerate((("KLUIS", "Diamantcentrum -2"), ("AFVAL  E19", "bos - Vilvoorde"), ("APPARTEMENT", "Torino"),
                                   ("DNA", "broodje / salami"), ("KASTICKET", "supermarkt - camera"), ("HUUR", "kantoor + kluis"))):
        im = Image.new("RGB", (900, 560), (238, 234, 222)); d = ImageDraw.Draw(im)
        d.line((0, 120, 900, 120), fill=(200, 60, 60), width=4)
        for y in range(180, 560, 56):
            d.line((0, y, 900, y), fill=(150, 180, 210), width=2)
        d.text((40, 24), t1, font=F(SERIFB, 76), fill=(25, 25, 35))
        d.text((40, 160), t2, font=F(COUR, 52), fill=(20, 30, 110))
        im.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(D, f"card_{k + 1}.jpg"), quality=88)


if __name__ == "__main__":
    cards()
    for s_ in range(1, 4):
        faxcover(s_)
    lcd()
    for s in range(1, 4):
        receipt(s); form(s); letter(s); briefke(s)
    print(sorted(os.listdir(D)))
