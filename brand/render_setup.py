# Seldom / Nvidia film: one-time render setup.
# In Blender: open film/nvidia_film.blend -> Scripting tab -> Open this file -> Run Script (play button).
# It switches every shot to your GPU, sets the output to one MP4 with sound, and saves the file.
import bpy

film = bpy.data.scenes["NVIDIA_FILM"]

# shots are linked from their own files (read-only) -> make the scenes local so their render settings can change
for sc in list(bpy.data.scenes):
    if sc.library is not None:
        sc.make_local()

# use the GPU (OptiX / CUDA / HIP / Metal / oneAPI, whichever this machine has)
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    except Exception:
        pass
for d in prefs.devices:
    d.use = True
for sc in bpy.data.scenes:
    try:
        sc.cycles.device = "GPU"
    except Exception:
        pass

# one MP4 with the voiceovers and sting sound
r = film.render
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"
r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.ffmpeg_preset = "GOOD"
r.ffmpeg.audio_codec = "AAC"
r.ffmpeg.audio_bitrate = 256
r.ffmpeg.audio_channels = "STEREO"
r.filepath = "//render/nvidia_film.mp4"
bpy.context.window.scene = film
bpy.ops.wm.save_mainfile()
print("Ready: GPU =", prefs.compute_device_type, "| output =", bpy.path.abspath(r.filepath))
