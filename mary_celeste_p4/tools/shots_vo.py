"""Part 4 shot table: the script words (verbatim, mary_celeste/SCRIPT.txt lines 31-38) split across the shots,
in order, plus the card note for CapCut and the camera move / handheld for the animated pass."""
SHOTS = [
    ("S01", "When the cargo is unloaded in Genoa,", "PLACE: GENOA, ITALY - 1873"),
    ("S02", "nine barrels are empty.", ""),
    ("S03", "For anyone trying to explain why Briggs might have put his family in a small boat,", "PERSON: BENJAMIN BRIGGS - CAPTAIN, MARY CELESTE"),
    ("S05", "those barrels are worth a closer look. If alcohol leaked into the hold, vapor could have collected below deck.", ""),
    ("S06", "The people above might have feared a fire or an explosion.", ""),
    ("S07", "An incident like that could give a captain a reason to get everyone away from a ship that otherwise looked capable of sailing.", ""),
    ("S08", "There are problems with that explanation.", ""),
    ("S09", "Deveau's party reports no smell of alcohol fumes.", ""),
    ("S10", "The main cargo hatch is still secured when they board.", ""),
    ("S11", "The nine empty barrels were described as red oak,", "LABELS: WHITE OAK (left) / RED OAK (right)"),
    ("S12", "a more porous wood than the white oak used for the others. That gives the missing alcohol a possible explanation on its own.", ""),
    ("S13", "Nobody can tell from the empty barrels whether they leaked slowly", ""),
    ("S14", "or whether anything happened suddenly enough", ""),
    ("S15", "to make ten people climb over the side.", ""),
    ("S16", "There's another clue Deveau finds before anyone counts the barrels.", ""),
    ("S17", "One of the ship's pumps has been taken apart.", ""),
    ("S18", "The ship had previously carried coal and had recently been refitted.", "PLACE: NEW YORK - OCTOBER 1872"),
    ("S19", "More than a century later, documentary researcher Anne MacGregor looks at those two facts alongside the dismantled pump.", "PERSON: ANNE MACGREGOR - DOCUMENTARY RESEARCHER"),
    ("S20", "Coal dust or debris from the work could have fouled it.", ""),
    ("S21", "A pump in pieces suggests someone may have been trying to find out why it wouldn't work.", ""),
    ("S22", "The record can't tell us what they found.", ""),
    ("S23", "MacGregor and oceanographer Phil Richardson also go back to the slate.", "PERSON: PHIL RICHARDSON - OCEANOGRAPHER"),
    ("S24", "They have two points to work with.", ""),
    ("S25", "The last recorded sighting of Santa Maria,", "LABEL: 25 NOV 1872 - 8 A.M."),
    ("S26", "and the place Deveau's ship found the Mary Celeste.", "LABEL: 38 20 N  17 15 W"),
    ("S27", "Using historical weather data, they test whether a ship with nobody steering could get from one to the other.", ""),
    ("S28", "It could.", ""),
    ("S29", "That matters because it puts a possible evacuation within sight of land.", ""),
    ("S30", "After a stretch of rough weather,", ""),
    ("S31", "Briggs may have been trying to judge how much water was coming in and whether the pumps could keep up.", ""),
    ("S32", "With the hold packed full of barrels, he couldn't simply look down and see what was happening at the bottom.", ""),
    ("S33", "If he believed the water was winning, Santa Maria would have been the one place he could see that offered a way off the ship.", ""),
    ("S34", "That's one possible reading of the evidence.", ""),
    ("S35", "The water Deveau measures is what's there when he boards.", "LABEL: 3 1/2 FEET"),
    ("S36", "We don't have the reading Briggs was working with, or even know that water was the danger that sent them over the side.", ""),
]

# animated pass: camera handheld amount (0 = tripod / dolly), people keep their storyboard pose with breathing
HANDHELD = {"S03": 0.4, "S06": 0.5, "S09": 0.4, "S10": 0.3, "S13": 0.5, "S14": 0.4, "S16": 0.4, "S17": 0.3, "S18": 0.3,
            "S21": 0.6, "S31": 0.6, "S33": 0.4, "S35": 0.4}
# exterior wides where the sea works the ship (camera not aboard)
SHIP_MOTION = ("S07", "S08", "S29", "S30", "S36")


def check(script_path):
    import re
    lines = open(script_path).read().splitlines()
    a = next(i for i, l in enumerate(lines) if l.startswith("When the cargo is unloaded in Genoa"))
    b = next(i for i, l in enumerate(lines) if "sent them over the side" in l)
    text = " ".join(lines[a:b + 1]).split()
    mine = " ".join(v for _, v, _ in SHOTS).split()
    return text == mine, len(text), len(mine)
