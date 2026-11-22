"""Seldom intro: 8 mini-film scripts (step 1, no renders) -> SELDOM_INTRO_CONCEPTS_P4.pdf"""
import os, sys
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")
pdfmetrics.registerFont(TTFont("CP", os.path.join(FONTS, "CourierPrime-Regular.ttf")))
pdfmetrics.registerFont(TTFont("CPB", os.path.join(FONTS, "CourierPrime-Bold.ttf")))
INK = colors.HexColor("#1d1f08"); LIME = colors.HexColor("#e2ff00"); GREY = colors.HexColor("#6b6b5f")
H1 = ParagraphStyle("h1", fontName="CPB", fontSize=22, leading=26, textColor=INK, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="CPB", fontSize=12, leading=15, textColor=INK, spaceBefore=6, spaceAfter=2)
B = ParagraphStyle("b", fontName="CP", fontSize=10, leading=13, textColor=INK)
S = ParagraphStyle("s", fontName="CP", fontSize=8.5, leading=11, textColor=GREY)
TB = ParagraphStyle("tb", fontName="CP", fontSize=9, leading=11.5, textColor=INK)
TH = ParagraphStyle("th", fontName="CPB", fontSize=9, leading=11.5, textColor=INK)

LOGO = "the Seldom wordmark exactly as designed (chunky lowercase, acid lime with a dark outline)"

FILMS = [
    dict(title="1. LAMP ROOM", length="12 s",
         log="A storm night. A lighthouse keeper climbs to the lamp room to clear salt from the great lens, and finds what the light has been guarding.",
         beats=[("0.0-3.0", "Wide, low, looking up the iron spiral stair. Rain streaks the tower windows.",
                 "The keeper, in an oilskin, climbs with a storm lantern in one hand, the other on the rail."),
                ("3.0-6.0", "Medium over his shoulder in the lamp room; the Fresnel lens fills the frame and throws prisms of light.",
                 "He sets the lantern down and wipes the salt-crusted brass housing with a rag."),
                ("6.0-9.0", "Close, still over his shoulder: the rag drags across an enamel plate bolted to the housing.",
                 "The salt comes away in one stroke. Under it is the plate."),
                ("9.0-12.0", "Locked off. The lens turns and its beam sweeps across him and out to sea.",
                 "He steps back. The beam comes round and holds on the plate. HOLD.")],
         logo=f"An old enamel maker's plate on the lens housing, {LOGO}, chipped at one corner, fixed with four brass screws.",
         sound="Wind howl, rain on glass, boots on iron treads, the rag squeaking on salt. The clockwork lens turns underneath. On the reveal, one deep foghorn note."),
    dict(title="2. DEAD LETTERS", length="11 s",
         log="A dead-letter office, 1920s, after midnight. One parcel has no address at all, only a label.",
         beats=[("0.0-3.0", "Wide, high angle: towering pigeon-hole walls, one green-shaded lamp, a single clerk at a long table.",
                 "She stamps envelopes RETURN TO SENDER in a steady rhythm."),
                ("3.0-6.0", "Medium side-light, half her face in shadow.",
                 "She lifts a small parcel bound in string, turns it and frowns: there's no address."),
                ("6.0-9.0", "Close over her hands (her sleeve and shoulder in frame), slow push-in.",
                 "She cuts the string with scissors and folds back the brown paper."),
                ("9.0-11.0", "Top-down, locked off.",
                 "Inside, on tissue, lies a printed card. The stamp hand stops mid-air. HOLD.")],
         logo=f"A letterpress card in the parcel, printed in {LOGO}, with ink slightly bitten into the cotton paper.",
         sound="The rhythm of the rubber stamp, a ticking wall clock, paper rustling. Scissors snip the string and the room tone drops to silence. A single clock tick on the reveal."),
    dict(title="3. THE LOCKSMITH", length="13 s",
         log="An abandoned bank vault. A locksmith cracks a safe nobody has opened in a hundred years.",
         beats=[("0.0-3.5", "Wide through dust in a torch beam: a cast-iron safe in a dead vault.",
                 "The locksmith kneels and presses a stethoscope to the door."),
                ("3.5-7.0", "Close on the dial, his ear and stethoscope in frame, shallow focus.",
                 "He turns the dial a click at a time, eyes closed, listening."),
                ("7.0-10.0", "Medium. He hauls the heavy handle down.",
                 "The bolts thunk back and the door swings open with a long groan."),
                ("10.0-13.0", "His torch moves in over his shoulder.",
                 "The safe is empty except for one enamel plaque on red velvet. His torch finds it and holds. HOLD.")],
         logo=f"A small enamel plaque lying on worn red velvet: {LOGO}.",
         sound="Dial clicks in close-up, magnified through the stethoscope; dust settling; three heavy bolt thunks; the hinge groan. Then near silence and his slow breath."),
    dict(title="4. SALVAGE", length="12 s",
         log="Grey dawn on a harbour. A crane lifts something out of the mud that has been down there for decades.",
         beats=[("0.0-3.0", "Wide from the quay: mist, gulls, a steam crane over black water.",
                 "A stevedore signals the crane up with his arm."),
                ("3.0-6.0", "Medium low. Chains tighten and a crate breaks the surface, pouring water.",
                 "He steadies the swinging crate with a boathook."),
                ("6.0-9.5", "Close, over his shoulder, as the crate settles on the stones.",
                 "He wipes the mud from its side with his sleeve in two strokes."),
                ("9.5-12.0", "Slow push-in, locked focus.",
                 "A stencilled word shows through the wet wood. He looks back at the water, then at the crate. HOLD.")],
         logo=f"Stencilled and painted on the crate's side: {LOGO}, faded and wet, the lime still bright under the mud.",
         sound="Gulls, the crane's chain rattle and steam hiss, a big water slough as the crate rises, sleeve on wet wood. On the reveal, a low ship's bell somewhere in the mist."),
    dict(title="5. PROJECTION BOOTH", length="13 s",
         log="A shuttered cinema. The projectionist finds a can in the vault that isn't on any list.",
         beats=[("0.0-3.0", "Wide: a film vault, racks of rusty cans, a single bulb.",
                 "The projectionist pulls an unlabelled can from the bottom shelf and blows off the dust."),
                ("3.0-6.5", "Medium in the booth, side-lit by the lamphouse.",
                 "He threads the film through the gate, closes it and pulls the lever."),
                ("6.5-10.0", "Over his shoulder through the booth port into the dark auditorium.",
                 "The beam fires across the empty seats; the countdown leader flickers on the screen."),
                ("10.0-13.0", "From the back row: the screen, the beam overhead, his silhouette in the port.",
                 "The leader ends on a single title card. The projector clatters on. HOLD.")],
         logo=f"A real title card on the film leader, projected on the screen: {LOGO} on black, with gate weave and dust flecks.",
         sound="Vault hum, the can lid scraping, a sprocket click-click as he threads, the projector motor spinning up into its steady clatter, a flutter of light on the screen, a reel ticking."),
    dict(title="6. ICE STATION", length="12 s",
         log="Polar night. A researcher finds a supply drum buried under the snow where no expedition ever camped.",
         beats=[("0.0-3.0", "Wide: a blizzard, a head torch bobbing toward camera across the ice.",
                 "The researcher, hooded, wades through the drifts toward a shape under the snow."),
                ("3.0-6.5", "Medium, low, with snow streaming through the head-torch beam.",
                 "She kneels and digs with gloved hands, then with an ice axe."),
                ("6.5-9.5", "Close over her shoulder.",
                 "She brushes the last snow from a steel drum's flank. Rust and paint show through."),
                ("9.5-12.0", "Locked off, the head-torch beam steady on the drum.",
                 "She sits back on her heels and her breath clouds in the beam. HOLD.")],
         logo=f"Hand-painted on a rusted steel drum, frosted at the edges: {LOGO}.",
         sound="Blizzard roar, crunching footsteps, the ice axe chipping, a glove brushing on steel. The wind drops out to her breathing on the reveal."),
    dict(title="7. DARKROOM", length="14 s",
         log="Red light. A photographer develops a print from a roll found in a dead man's camera.",
         beats=[("0.0-3.0", "Wide: a darkroom under the red safelight, the enlarger glowing and trays lined up.",
                 "The photographer slides the exposed paper into the developer tray with tongs."),
                ("3.0-7.0", "Medium, side-lit red, half his face in shadow.",
                 "He rocks the tray gently and stares into it."),
                ("7.0-11.0", "Top-down on the tray, slow push-in, his tongs and arm in frame.",
                 "An image rises out of the white paper: a painted sign on a brick wall, shot at night."),
                ("11.0-14.0", "Locked off. He lifts the dripping print to the light and pins it to the drying line.",
                 "The sign in the photograph is the logo. HOLD.")],
         logo=f"A real sign painted on a wall, photographed and appearing in the developing print: {LOGO} (the print keeps its colour; a colour process).",
         sound="The safelight hum, liquid lapping in the tray, a timer ticking, drips. The clothes-pin clicks onto the line on the reveal."),
    dict(title="8. THE ARCHIVIST", length="12 s",
         log="A deep archive after hours. A drawer that should be empty isn't.",
         beats=[("0.0-3.0", "Wide down an endless corridor of card-index cabinets, lit by one desk lamp at the far end.",
                 "The archivist walks the aisle from behind, running a finger along the drawer labels."),
                ("3.0-6.0", "Medium. She stops at a drawer with a blank label holder.",
                 "She tries it; it's stuck. She pulls harder."),
                ("6.0-9.0", "Close over her shoulder as the drawer slides out in a puff of dust.",
                 "It holds no cards, only a single folded file."),
                ("9.0-12.0", "Top-down on the opened file, under the lamp.",
                 "She opens the cover. Inside is a stamped plate. She glances back down the dark aisle. HOLD.")],
         logo=f"An embossed and enamelled file plate inside the folder: {LOGO}.",
         sound="Distant ventilation, footsteps on parquet, a fingernail along brass label holders. The stuck drawer shudders, then a dust puff. On the reveal, a far-off door closes somewhere in the stacks."),
]


def build(path):
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=16 * mm, rightMargin=16 * mm, topMargin=13 * mm, bottomMargin=12 * mm,
                            title="Seldom intro - 8 mini-film scripts (P4)", author="Seldom studio")
    st = []
    logo = "/tmp/claude-0/-home-user-Muhammed/27996c0c-ba9f-5c16-8812-a69353556380/scratchpad/logo/logo.png"
    st.append(Paragraph("SELDOM INTRO - 8 MINI-FILM SCRIPTS", H1))
    st.append(Paragraph("Step 1 for the hub's pick. Scripts only, no renders. From the Part 4 session.", S))
    st.append(Spacer(1, 6))
    if os.path.exists(logo):
        from PIL import Image as PI
        im = PI.open(logo).crop((300, 790, 1675, 1210)); cpath = os.path.join(HERE, "logo_crop.png"); im.save(cpath)
        st.append(Image(cpath, width=70 * mm, height=70 * mm * 420 / 1375))
    st.append(Spacer(1, 6))
    for t in ["Each intro is a short scene, 11-14 s, with a tiny story: one person doing one real action that ends in a discovery.",
              "The logo is never animated. It is a physical object in the scene (enamel, stencil, letterpress, film leader, paint, emboss) "
              "that the person uncovers, and the last shot holds on it for about 2-3 s.",
              "All films follow the house rules: a person in frame whenever a hand is shown; cinematic camera (no face close-ups, side-light "
              "or over the shoulder); Atrium-quality lighting and colour; physically real props; no flat 2D; no clipping; a mystery mood.",
              "Sound: a full bed in every film (room tone, weather), one effect for every action, and a single 'reveal' sound on the logo. No music needed."]:
        st.append(Paragraph("- " + t, B)); st.append(Spacer(1, 3))
    st.append(Spacer(1, 6))
    rows = [[Paragraph("Film", TH), Paragraph("Length", TH), Paragraph("Logo on", TH)]]
    for f in FILMS:
        rows.append([Paragraph(f["title"], TB), Paragraph(f["length"], TB), Paragraph(f["logo"].split(":")[0].split(",")[0], TB)])
    t = Table(rows, colWidths=[60 * mm, 22 * mm, 170 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8e6")])]))
    st.append(t)
    for f in FILMS:
        st.append(PageBreak())
        st.append(Paragraph(f"{f['title']}  <font size=11 color='#6b6b5f'>({f['length']})</font>", H1))
        st.append(Paragraph(f["log"], B))
        st.append(Paragraph("Shot list", H2))
        rows = [[Paragraph("Time (s)", TH), Paragraph("Shot / camera", TH), Paragraph("What the person does", TH)]]
        for tm, cam, act in f["beats"]:
            rows.append([Paragraph(tm, TB), Paragraph(cam, TB), Paragraph(act, TB)])
        t = Table(rows, colWidths=[22 * mm, 115 * mm, 115 * mm])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8e6")]),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        st.append(t)
        st.append(Paragraph("Where the logo appears", H2)); st.append(Paragraph(f["logo"], B))
        st.append(Paragraph("Sound", H2)); st.append(Paragraph(f["sound"], B))
    doc.build(st)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "SELDOM_INTRO_CONCEPTS_P4.pdf"))
    print("ok")
