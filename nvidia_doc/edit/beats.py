"""Beat sheet for "The Spy Allegations Rocking Nvidia".

Every narration sentence (verbatim) is assigned to a beat. A beat has:
  shot   : the visual (a 3D plate / hero shot from scenes/, or a motion-graphics template from mograph/)
  gfx    : on-screen text layers (cards, labels, dates, quotes, source tags)
  tag    : "ILLUSTRATION" / "RECONSTRUCTION" when the picture is a recreation, never presented as real footage
  src    : on-screen attribution, matching how the narration attributes the claim

Editorial guardrails baked into the design:
  * No likeness of any real person. People are represented by empty chairs, silhouettes or not at all.
  * No company or news-outlet logos. Names appear only as plain text in our own typography.
  * Documents (memo, letter, filings) are stylised illustrations with redaction bars; no invented text is
    presented as a real document.
  * Allegations stay attributed exactly as the script attributes them.

Timing: until the real voiceover arrives, a beat lasts (words / 130 wpm) + its `pad`. edit/align.py replaces
these estimates with word timestamps from the recorded VO.
"""

WPM = 130.0


def B(id, text, shot, gfx=(), tag=None, src=None, pad=0.0, ch=None):
    return dict(id=id, text=text, shot=shot, gfx=list(gfx), tag=tag, src=src, pad=pad, ch=ch)


# ----------------------------------------------------------------------------- shot helpers
def S3(scene, move="push", **kw):        # 3D scene (plate rendered once + depth, or a hero animation)
    return dict(kind="3d", scene=scene, move=move, **kw)


def MG(template, **kw):                  # motion-graphics template
    return dict(kind="mg", template=template, **kw)


def OVER(scene, template, move="push", **kw):   # graphics composited over a (blurred/darkened) 3D plate
    return dict(kind="over", scene=scene, template=template, move=move, **kw)


# ----------------------------------------------------------------------------- gfx helpers
def quote(text, who, when):          return dict(kind="quote", text=text, who=who, when=when)
def date(text, pos="tl"):            return dict(kind="date", text=text, pos=pos)
def label(text, sub=None, pos="bl"): return dict(kind="label", text=text, sub=sub, pos=pos)
def title(text, sub=None):           return dict(kind="title", text=text, sub=sub)
def big(text, sub=None):             return dict(kind="big", text=text, sub=sub)
def card(head, body, kind="statement"): return dict(kind=kind, head=head, body=body)


BEATS = [
    # ======================================================================== COLD OPEN
    B("o01", "“I was unfaithful to my wife.”",
      OVER("chip_macro", "quote_card", move="drift_dark", hold_black=0.6),
      [quote("I was unfaithful to my wife.", "JENSEN HUANG · EMAIL TO NVIDIA EMPLOYEES", "NOV 8, 2026")],
      src="NVIDIA", pad=1.2, ch="open"),
    B("o02", "That’s what Nvidia CEO Jensen Huang tells his employees on November eighth.",
      S3("chip_macro", move="sweep_reveal"),
      [date("NOV 8, 2026"), label("NVIDIA", "Chief executive Jensen Huang writes to employees")]),
    B("o03", "The same day, Nvidia opens an independent investigation into whether a foreign intelligence service targeted him.",
      S3("boardroom", move="slow_push"),
      [date("NOV 8, 2026"), label("INDEPENDENT INVESTIGATION", "Opened by Nvidia’s board")], src="NVIDIA BOARD STATEMENT"),
    B("o04", "The woman at the center of the allegation is Alice Huang.",
      S3("datacenter", move="silhouette_aisle"),
      [label("ALICE HUANG", "At the center of the allegation", pos="name")], tag="ILLUSTRATION"),
    B("o05", "She comes from the other side of Nvidia’s business.",
      S3("datacenter", move="rack_lights"), []),
    B("o06", "The company she helps build buys the kinds of chips Washington is trying to keep out of China.",
      MG("map", view="us_china", routes=[("WASHINGTON", "BEIJING", "blocked")], chips=True),
      [label("EXPORT CONTROLS", "Advanced AI chips restricted from China")], pad=0.4),
    B("o07", "", MG("title_card"), [title("THE SPY ALLEGATIONS ROCKING NVIDIA")], pad=5.0),

    # ======================================================================== CHAPTER ONE
    B("c1_00", "", MG("chapter_card", number="ONE", name="FOLLOW THE CHIPS", bg="gpu_module"), pad=3.5, ch="1"),
    B("c1_01", "In October 2022, the United States announces a new set of export controls.",
      OVER("capitol", "document_stamp", move="slow_push", doc="export_rule"),
      [date("OCT 2022"), label("U.S. COMMERCE DEPARTMENT", "New export controls on advanced computing")], src="U.S. COMMERCE DEPARTMENT"),
    B("c1_02", "Shipments of certain advanced processors to China are restricted.",
      MG("map", view="pacific", routes=[("UNITED STATES", "CHINA", "blocked")], chips=True), []),
    B("c1_03", "Washington says the same computing power that drives commercial research can also help China build more advanced military systems.",
      MG("dual_use"), [label("DUAL USE", "Commercial research  ·  Military systems")], src="U.S. COMMERCE DEPARTMENT"),
    B("c1_04", "One of the chips caught up in those restrictions is Nvidia’s H100.",
      S3("gpu_module", move="hero_orbit"), [label("H100", "Data-center AI accelerator", pos="spec")]),
    B("c1_05", "Put enough of them together in a data center and they can split the work of training an AI model across a whole bank of machines.",
      S3("datacenter", move="dolly_aisle", pulses=True), [label("TRAINING", "One model, split across thousands of chips")], pad=0.3),
    B("c1_06", "For a company trying to get that computing power, there are two ways to go about it.",
      MG("split_choice", left="BUY", right="RENT"), []),
    B("c1_07", "You can buy the hardware and install it yourself.",
      MG("split_choice", left="BUY", right="RENT", focus="left"), [label("OPTION 1", "Buy the hardware · install it yourself")]),
    B("c1_08", "Or you can pay to use someone else’s.",
      MG("split_choice", left="BUY", right="RENT", focus="right"), [label("OPTION 2", "Rent someone else’s · in the cloud")]),
    B("c1_09", "The machines can be in one country and the person sending them work can be in another.",
      MG("map", view="asia", routes=[("SHANGHAI", "SINGAPORE", "data")], remote=True), []),
    B("c1_10", "The data moves. The chips stay in the rack.",
      OVER("datacenter", "data_moves", move="locked_rack"), [], pad=0.6),
    B("c1_11", "That distinction matters because a shipping record can tell you where a machine was delivered.",
      MG("records", focus="shipping"), [label("SHIPPING RECORD", "Where the machine was delivered")]),
    B("c1_12", "A different set of records would tell you who rented it and where they connected from.",
      MG("records", focus="access"), [label("ACCESS RECORDS", "Who rented it · where they connected from")], pad=0.4),
    B("c1_13", "That’s the business Alice Huang moves into. She comes from Shanghai’s investment world.",
      S3("shanghai", move="night_drift"), [label("SHANGHAI", "Finance and investment"), label("ALICE HUANG", None, pos="name")], tag="ILLUSTRATION"),
    B("c1_14", "In 2023, she takes control of a Singapore company called Megaspeed.",
      MG("structure", step=1), [date("2023")], src="REUTERS"),
    B("c1_15", "It began as a subsidiary of a video game developer. It becomes an Nvidia cloud partner.",
      MG("structure", step=2), [], src="REUTERS"),
    B("c1_16", "By the end of 2023, a Singapore company called SwiftData has taken ownership of Megaspeed.",
      MG("structure", step=3), [date("END OF 2023")], src="REUTERS", pad=0.3),
    B("c1_17", "Look at Megaspeed’s filings.",
      MG("filings", step=0), [label("CORPORATE FILINGS", "Megaspeed")], src="REUTERS"),
    B("c1_18", "In 2023, the company reports thirty-three million dollars in assets. A year later, it reports three billion.",
      MG("filings", step=1), [], src="REUTERS", pad=1.0),
    B("c1_19", "And when Alice and a business partner pitch a new data center project to investors in early 2025, an investor tells the Financial Times that the pair makes a point of how easily they can get Nvidia GPUs.",
      OVER("datacenter_build", "quote_card_small", move="slow_push"),
      [date("EARLY 2025"), quote("How easily they can get Nvidia GPUs", "AN INVESTOR, AS REPORTED BY THE FINANCIAL TIMES", "")],
      src="FINANCIAL TIMES", tag="ILLUSTRATION"),
    B("c1_20", "The investor says they name Alibaba as a client for the project.",
      MG("structure", step=4), [label("NAMED AS A CLIENT", "Alibaba · according to the investor")], src="FINANCIAL TIMES"),
    B("c1_21", "The chip deliveries leave their own trail.",
      S3("port", move="crane_rise"), [], tag="ILLUSTRATION"),
    B("c1_22", "Shipping records reviewed by Reuters show Megaspeed’s Indonesian subsidiary importing Nvidia hardware between 2024 and 2026. The records include H100s.",
      MG("map", view="sea", routes=[("ORIGIN", "INDONESIA", "shipping")], manifest=True),
      [date("2024 — 2026"), label("SHIPPING RECORDS", "Megaspeed’s Indonesian subsidiary · includes H100s")], src="REUTERS"),
    B("c1_23", "Those shipments establish that the hardware reached Indonesia.",
      S3("port", move="container_push"), [label("INDONESIA", "Delivered")], tag="ILLUSTRATION"),
    B("c1_24", "The next question is who could use it, and from where.",
      MG("map", view="asia", routes=[("INDONESIA", "?", "unknown")], remote=True), [], pad=0.8),
    B("c1_25", "By October 2025, the New York Times reports that U.S. authorities are looking into whether Megaspeed helped Chinese companies get access to advanced chips covered by American export controls.",
      MG("headlines", step=1), [date("OCT 2025")], src="THE NEW YORK TIMES"),
    B("c1_26", "Singapore police confirm their own investigation into possible breaches of Singapore law.",
      MG("headlines", step=2), [], src="SINGAPORE POLICE FORCE"),
    B("c1_27", "Megaspeed denies illicit activity involving chips.",
      MG("headlines", step=3), [], src="MEGASPEED", pad=0.5),
    B("c1_28", "On October tenth, reporters from the Straits Times visit Megaspeed’s office on the seventh floor of Singapore’s Ocean Financial Centre.",
      S3("singapore_tower", move="tower_tilt"), [date("OCT 10"), label("OCEAN FINANCIAL CENTRE", "Singapore · 7th floor")], src="THE STRAITS TIMES", tag="ILLUSTRATION"),
    B("c1_29", "The glass door is locked.",
      S3("office_door", move="door_push"), [], tag="RECONSTRUCTION", src="THE STRAITS TIMES", pad=0.5),
    B("c1_30", "They can see two gray armchairs in reception.",
      S3("office_door", move="through_glass"), [], tag="RECONSTRUCTION", pad=0.5),
    B("c1_31", "The company’s nameplate is still there.",
      S3("office_door", move="nameplate"), [], tag="RECONSTRUCTION", pad=1.5),

    # ======================================================================== CHAPTER TWO
    B("c2_00", "", MG("chapter_card", number="TWO", name="THE MEMO", bg="memo_desk"), pad=3.5, ch="2"),
    B("c2_01", "At the 2024 Computex trade show in Taiwan, a server manufacturer called Gigabyte throws a party.",
      S3("party", move="bokeh_drift"), [date("2024"), label("COMPUTEX · TAIWAN", "A party thrown by server maker Gigabyte")], tag="ILLUSTRATION"),
    B("c2_02", "Its servers use Nvidia chips.",
      S3("gpu_module", move="server_tray"), []),
    B("c2_03", "A person who attends tells Reuters that both Alice and Jensen are there.",
      S3("party", move="rack_focus"), [], src="REUTERS", tag="ILLUSTRATION"),
    B("c2_04", "In a photo posted on LinkedIn, the two are sitting side by side.",
      S3("party", move="two_chairs"), [label("A PHOTO POSTED ON LINKEDIN", "The two sit side by side")], src="REUTERS", tag="RECONSTRUCTION", pad=0.5),
    B("c2_05", "Then there’s video.",
      MG("broadcast_frame", state="noise"), [], pad=0.4),
    B("c2_06", "On May twenty-second, 2025, Taiwanese television footage shows a group dinner at a restaurant in Taipei.",
      OVER("restaurant", "broadcast_frame", move="tv_zoom"), [date("MAY 22, 2025"), label("TAIPEI", "A group dinner, filmed by local television")], tag="RECONSTRUCTION"),
    B("c2_07", "Reuters later compares the footage with a separate photograph and identifies Alice at the table. Jensen is there too.",
      MG("compare_frames"), [label("MATCHED", "Footage compared with a separate photograph")], src="REUTERS", tag="RECONSTRUCTION"),
    B("c2_08", "Their companies have a clear business connection.",
      MG("connection"), []),
    B("c2_09", "The espionage allegation traces back to a document circulating in Washington.",
      S3("memo_desk", move="lamp_on"), [], tag="ILLUSTRATION", pad=0.5),
    B("c2_10", "In the spring of 2026, according to the New York Times, a memo circulates among senior officials in the Trump administration.",
      S3("memo_desk", move="memo_push"), [date("SPRING 2026"), label("THE MEMO", "Circulated among senior administration officials")], src="THE NEW YORK TIMES", tag="ILLUSTRATION"),
    B("c2_11", "People briefed on the intelligence tell the paper that China’s Ministry of State Security recruited Alice Huang to gather information on Jensen.",
      OVER("memo_desk", "memo_redact", move="memo_close", line="recruited Alice Huang to gather information on Jensen"),
      [], src="THE NEW YORK TIMES · PEOPLE BRIEFED ON THE INTELLIGENCE", tag="ILLUSTRATION"),
    B("c2_12", "The reported goal includes learning more about America’s advanced AI chips and potentially getting Nvidia to push for broader sales to China.",
      OVER("memo_desk", "memo_redact", move="memo_close2", line="learning more about America’s advanced AI chips"),
      [label("THE REPORTED GOAL", "Chip knowledge · broader sales to China")], src="THE NEW YORK TIMES", tag="ILLUSTRATION", pad=0.4),
    B("c2_13", "The allegation puts a different kind of information at stake.",
      S3("chip_macro", move="dark_orbit"), []),
    B("c2_14", "A chip is something you can trace through a shipment.",
      MG("trace_vs_talk", focus="chip"), []),
    B("c2_15", "A company’s plans for what it wants to sell, or what it’s asking Washington to approve, can travel in a conversation.",
      MG("trace_vs_talk", focus="talk"), [], pad=0.4),
    B("c2_16", "Consider how much a single decision in Washington can change.",
      S3("capitol", move="dusk_push"), []),
    B("c2_17", "In April 2025, the U.S. government tells Nvidia it needs a license to sell a different chip, the H20, into China.",
      OVER("gpu_module", "document_stamp", move="hero_orbit", doc="license"), [date("APRIL 2025"), label("H20", "Now needs a U.S. license to sell into China", pos="spec")], src="NVIDIA SEC FILING"),
    B("c2_18", "Nvidia later reports a four and a half billion dollar charge tied to inventory and purchase commitments for that chip.",
      MG("big_number", value=4.5, unit="BILLION", prefix="$"), [label("CHARGE", "Inventory and purchase commitments for the H20")], src="NVIDIA SEC FILING", pad=0.5),
    B("c2_19", "Knowing which processors Washington might clear for sale, and when, could shape where a customer spends billions.",
      MG("timeline_bets"), [], pad=0.4),
    B("c2_20", "On October twenty-ninth, the Times makes the suspected operation public.",
      MG("headlines", step=4), [date("OCT 29")], src="THE NEW YORK TIMES"),
    B("c2_21", "Nvidia says its CEO routinely meets with customers and that its regional cloud customers receive ordinary business information.",
      MG("statements", who="NVIDIA"), [], src="NVIDIA"),
    B("c2_22", "China’s Foreign Ministry later rejects the spying allegation.",
      MG("statements", who="CHINA’S FOREIGN MINISTRY"), [], src="MINISTRY OF FOREIGN AFFAIRS OF CHINA"),
    B("c2_23", "Reuters says it was unable to verify it independently, and reporters at both Reuters and the Financial Times were unable to reach Alice for comment.",
      MG("statements", who="UNVERIFIED"), [], src="REUTERS · FINANCIAL TIMES", pad=0.8),

    # ======================================================================== CHAPTER THREE
    B("c3_00", "", MG("chapter_card", number="THREE", name="BEHIND CLOSED DOORS", bg="doors"), pad=3.5, ch="3"),
    B("c3_01", "In Washington, three House committee chairs send Jensen a letter.",
      S3("capitol", move="night_rise"), [label("U.S. HOUSE OF REPRESENTATIVES", "Three committee chairs")], src="HOUSE FOREIGN AFFAIRS COMMITTEE"),
    B("c3_02", "They want him to brief them behind closed doors about his contacts with Alice Huang and what Nvidia does to protect itself from foreign espionage.",
      OVER("memo_desk", "letter", move="letter_push"), [label("REQUEST", "A private briefing")], tag="ILLUSTRATION"),
    B("c3_03", "They request November eighteenth.",
      MG("calendar", day=18), [date("NOV 18")], pad=0.6),
    B("c3_04", "Four days after the letter is dated, Jensen sends the email admitting to an affair.",
      MG("calendar", day=8, mark="email"), [date("NOV 8")]),
    B("c3_05", "He says he’ll cooperate fully with the board’s investigation. His message leaves the other person unnamed.",
      S3("boardroom", move="empty_chair"), [], src="NVIDIA"),
    B("c3_06", "The Times and the Financial Times identify her as Alice Huang.",
      MG("name_reveal"), [], src="THE NEW YORK TIMES · FINANCIAL TIMES", pad=0.5),
    B("c3_07", "When Nvidia’s board announces its investigation, it says it has no reason to believe company secrets or national security were compromised.",
      OVER("boardroom", "statement_quote", move="slow_push", text="No reason to believe company secrets or national security were compromised."),
      [], src="NVIDIA BOARD OF DIRECTORS"),
    B("c3_08", "The next day, President Trump says the FBI is looking into the matter.",
      MG("statements", who="THE WHITE HOUSE"), [date("NOV 9")], src="AP"),
    B("c3_09", "On November tenth, Nvidia names the lawyer who will lead the outside investigation. Joon H. Kim is a former acting U.S. attorney in Manhattan.",
      S3("boardroom", move="dossier"), [date("NOV 10"), label("JOON H. KIM", "Former acting U.S. attorney, Manhattan · leads the outside investigation", pos="name")], src="NVIDIA"),
    B("c3_10", "A shareholder lawsuit adds another question.",
      S3("courthouse", move="steps_rise"), [label("SHAREHOLDER LAWSUIT", None)], tag="ILLUSTRATION"),
    B("c3_11", "The complaint accuses Nvidia and its CEO of misleading investors about the risks surrounding the company’s dealings with Megaspeed.",
      OVER("courthouse", "complaint_doc", move="slow_push"), [], src="AP"),
    B("c3_12", "Those allegations are now before a court.",
      S3("courthouse", move="columns_drift"), [], pad=0.5),
    B("c3_13", "As of November eleventh, there’s been no public finding that Megaspeed broke export rules.",
      MG("open_questions", step=1), [date("NOV 11, 2026")]),
    B("c3_14", "Nvidia’s board has yet to publish its conclusions.",
      MG("open_questions", step=2), []),
    B("c3_15", "And the evidence behind the reported intelligence assessment is still out of public view.",
      MG("open_questions", step=3), [], pad=0.6),
    B("c3_16", "If Jensen gives Congress the briefing it requested, it will take place behind closed doors.",
      S3("doors", move="corridor_push"), [], tag="ILLUSTRATION"),
    B("c3_17", "The question on the other side of those doors is the one the public still can’t answer.",
      S3("doors", move="doors_close"), [], tag="ILLUSTRATION", pad=0.4),
    B("c3_18", "What, if anything, reached Beijing?",
      MG("final_question"), [title("WHAT, IF ANYTHING, REACHED BEIJING?")], pad=3.0),
    B("end", "", MG("sources"), [], pad=8.0, ch="end"),
]


def est_duration(b):
    words = len(b["text"].split())
    return words / WPM * 60.0 + b["pad"]


def check_coverage(script_path):
    """Assert the beats reproduce the narration word-for-word, in order."""
    import re
    raw = open(script_path, encoding="utf8").read()
    body = " ".join(l for l in raw.splitlines() if not l.startswith("##"))
    norm = lambda s: re.findall(r"[A-Za-z0-9’'\-]+", s.lower())
    want = norm(body)
    got = norm(" ".join(b["text"] for b in BEATS))
    assert want == got, next((f"first mismatch at word {i}: script={w!r} beats={g!r}" for i, (w, g) in enumerate(zip(want, got)) if w != g), "length differs")
    return len(want)


if __name__ == "__main__":
    import os
    n = check_coverage(os.path.join(os.path.dirname(__file__), "script.txt"))
    tot = sum(est_duration(b) for b in BEATS)
    scenes = sorted({b["shot"].get("scene") for b in BEATS if b["shot"].get("scene")} |
                    {b["shot"].get("bg") for b in BEATS if b["shot"].get("bg")})
    temps = sorted({b["shot"].get("template") for b in BEATS if b["shot"].get("template")})
    print(f"{len(BEATS)} beats · {n} narration words · estimated runtime {tot // 60:.0f}:{tot % 60:04.1f}")
    print("3D scenes:", ", ".join(scenes))
    print("templates:", ", ".join(temps))
