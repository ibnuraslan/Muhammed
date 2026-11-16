# shared paths for TenDimes build scripts
import os
SCR = "/tmp/claude-0/-home-user-Muhammed/bd92c549-00ff-528d-8132-9ca22d5ecf23/scratchpad"
REPO = "/home/user/Muhammed/blender"
PIPE = REPO + "/pipeline"
V = REPO + "/TenDimes_v001"
BUILD = SCR + "/build"
ASSETS = SCR + "/assets"
os.makedirs(BUILD, exist_ok=True)
