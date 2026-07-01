"""One-time setup: fetch static ffmpeg (if not on PATH) + Kokoro model + fonts -> tools/paths.json.
Idempotent. Run from your SHORT working dir."""
import os, sys, json, shutil, zipfile, platform, urllib.request

CWD = os.getcwd(); TOOLS = os.path.join(CWD, "tools"); os.makedirs(TOOLS, exist_ok=True)

def dl(url, dst):
    if os.path.isfile(dst) and os.path.getsize(dst) > 0:
        print("have", os.path.basename(dst)); return
    print("downloading", url)
    urllib.request.urlretrieve(url, dst)
    print("  ->", dst, os.path.getsize(dst), "bytes")

# ---- ffmpeg / ffprobe ----
ff = shutil.which("ffmpeg"); fp = shutil.which("ffprobe")
if not (ff and fp):
    if platform.system() == "Windows":
        z = os.path.join(TOOLS, "ffmpeg.zip")
        dl("https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip", z)
        with zipfile.ZipFile(z) as zf: zf.extractall(os.path.join(TOOLS, "ffmpeg"))
        for root, _, files in os.walk(os.path.join(TOOLS, "ffmpeg")):
            if "ffmpeg.exe" in files:
                ff = os.path.join(root, "ffmpeg.exe"); fp = os.path.join(root, "ffprobe.exe")
    else:
        sys.exit("Install ffmpeg (apt/brew) so 'ffmpeg' + 'ffprobe' are on PATH, then re-run.")
print("ffmpeg:", ff)

# ---- Kokoro model + voices ----
km = os.path.join(TOOLS, "kokoro-v1.0.onnx"); kv = os.path.join(TOOLS, "voices-v1.0.bin")
base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
dl(base + "kokoro-v1.0.onnx", km); dl(base + "voices-v1.0.bin", kv)

# ---- fonts (copied into tools/ so drawtext can use a relative path) ----
def findfont(names):
    bases = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")] if platform.system()=="Windows" \
            else ["/usr/share/fonts", "/Library/Fonts", "/System/Library/Fonts"]
    for b in bases:
        for n in names:
            p = os.path.join(b, n)
            if os.path.isfile(p): return p
        for root, _, files in os.walk(b if os.path.isdir(b) else "."):
            for n in names:
                if n in files: return os.path.join(root, n)
    return None
fr = findfont(["arial.ttf","Arial.ttf","DejaVuSans.ttf","Helvetica.ttc"])
fb = findfont(["arialbd.ttf","Arial Bold.ttf","DejaVuSans-Bold.ttf"])
if fr: shutil.copy(fr, os.path.join(TOOLS, "font.ttf"))
if fb: shutil.copy(fb, os.path.join(TOOLS, "fontb.ttf"))
elif fr: shutil.copy(fr, os.path.join(TOOLS, "fontb.ttf"))
# symbol-capable font (checkmark ✓ etc.) — Arial lacks these glyphs
sym = findfont(["seguisym.ttf","Segoe UI Symbol.ttf","DejaVuSans.ttf",
                "NotoSansSymbols2-Regular.ttf","Arial Unicode.ttf","AppleSymbols.ttf"])
if sym: shutil.copy(sym, os.path.join(TOOLS, "symbol.ttf"))
print("fonts:", fr, fb, "| symbol:", sym)

json.dump({"ffmpeg":ff,"ffprobe":fp,"kokoro_model":km,"kokoro_voices":kv,
           "font":os.path.join(TOOLS,"font.ttf"),"fontb":os.path.join(TOOLS,"fontb.ttf")},
          open(os.path.join(TOOLS,"paths.json"),"w"), indent=1)
print("setup done -> tools/paths.json")
