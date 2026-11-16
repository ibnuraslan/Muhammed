# shared paths for FridgeTenYears build scripts
import os
SCR = "/tmp/claude-0/-home-user-Muhammed/afc59c0d-b246-5d2b-9c60-d9e8e627f8a2/scratchpad"
REPO = "/home/user/Muhammed/blender"
PIPE = REPO + "/pipeline"
V = REPO + "/FridgeTenYears_v001"
BUILD = SCR + "/build"
MODELS = SCR + "/models"
os.makedirs(BUILD, exist_ok=True)
