# Shared layout constants for ElectricianPolice (exec'd by 02 and 03).
from mathutils import Vector
V = lambda *a: Vector(a)
ASSETS = "/tmp/claude-0/-home-user-Muhammed/60302108-5c41-54cc-ade1-198d9ab30d69/scratchpad"
import os
ASSETS = os.environ.get("EP_ASSETS", ASSETS)
BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__ if "__file__" in dir() else "."))), "build")

FPS = 60
def F(t):
    return int(round(1 + t * FPS))
BEATS = [(1, 0.0, "He was riding his motorcycle without a helmet"), (2, 2.8, "and the police gave him a fine"),
         (3, 4.7, "But he was an electrician"), (4, 6.6, "with access to the power grid"),
         (5, 8.4, "So he checked the records"), (6, 10.3, "and found that the police station hadn't paid"),
         (7, 14.9, "And that bill was huge"), (8, 17.6, "so he cut off their power"),
         (9, 19.4, "For five hours, the police station sat in the dark"), (10, 20.5, "For five hours"),
         (11, 23.0, "all because they fined the wrong guy")]
FRAME_END = 1560

ROAD_W = 8.0             # road x in [-4, 4]; traffic keeps left, heading +Y uses x < 0
BUILD_X = 7.0            # building fronts at |x| = 7
STOP = V(-2.6, 21.0, 0)  # where the bike stops
OFFICER_SPOT = V(-4.6, 23.2, 0)
GATE = V(8.0, 24.0, 0)   # substation gate in the east fence (fence line x = 8)
SUB = dict(x0=8.0, x1=34.0, y0=10.0, y1=46.0)
OFFICE = dict(x0=17.0, x1=26.0, y0=38.0, y1=46.0, h=3.2)   # utility office; window in the south wall (y0)
OFFICE_WIN = V(21.5, 38.0, 1.55)                           # centre of the window opening
DESK = V(21.5, 43.6, 0)        # desk centre (desk faces -Y: the man sits on its south side facing +Y)
CHAIR = V(21.5, 42.72, 0)
CABINET = V(25.62, 43.2, 0)    # switchgear on the east wall, door facing -X
STATION = dict(x0=-19.0, x1=-7.0, y0=50.0, y1=64.0, h=7.0)  # police station, facade at x = -7 facing +X (the road)
ST_DOOR = V(-7.0, 57.0, 0)
ST_WIN_Y = [51.6, 53.9, 60.1, 62.4]   # window centres along y (ground and first floor)
CLOCK_POS = V(-18.85, 57.0, 2.35)     # wall clock on the back wall, facing +X
