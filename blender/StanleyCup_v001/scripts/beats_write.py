"""python3 beats_write.py <out.json> : writes beats.json from layout.py"""
import sys, json, os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "layout.py")).read().split("from mathutils")[0]
FPS = 60
BEATS = [(1, 0.0, "A bullet was fired at the house"), (2, 2.3, "tore straight through the wall"), (3, 4.5, "Inside, a woman and her fiance"),
         (4, 6.5, "froze as the stray bullet"), (5, 10.1, "her trusty tumbler, full of ice water"), (6, 16.2, "the bullet slammed into the cup"),
         (7, 21.4, "dropped harmlessly to the floor"), (8, 23.6, "saving her life")]
json.dump([{"beat": b, "frame": 1 + round(t * FPS), "first_words": w} for b, t, w in BEATS], open(sys.argv[1], "w"), indent=1)
