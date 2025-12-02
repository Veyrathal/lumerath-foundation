from dotenv import load_dotenv
load_dotenv()    # <-- Loads your .env file with the API key

from flask import Flask, jsonify, send_from_directory, abort 
from pathlib import Path
import json
import os
import alignment_layer 

from flask import Flask, render_template, redirect, url_for
from communion import communion_bp, init_db
from foundation import foundation_ui

app = Flask(__name__)
#@app.route("/")
#def lumerath_home():
#    return redirect(url_for("communion.home"))

app.register_blueprint(communion_bp)
app.register_blueprint(foundation_ui)

@app.route("/")
def communion():
    return render_template("communion.html")

#@app.route("/communion")
#def communion():
#    return render_template("communion.html")

#@app.route("/home")
#def legacy_home():
#    return redirect(url_for("lumerath_home"))
     
@app.route("/ping")
def ping():
    return "OK", 200

#@app.route("/")
#def home():
  #  return redirect(url_for("communion.html"))

#@app.route("/communion", endpoint="communion.root")
#def communion_root():
#    return redirect(url_for("communion.home"))

#@app.route("/", endpoint="root")
#def root():
#    return redirect(url_for("communion.home"))

ROOT = Path(__file__).parent
CODEX_DIR = ROOT / "storage" / "codex"
ASSETS_DIR = ROOT / "storage" / "assets"

CODEX_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
# --- add imports ---
from werkzeug.utils import secure_filename
from flask import request, render_template, abort
import json
# --------------------
ALLOWED_JSON = {".json"}
ALLOWED_IMG  = {".png", ".jpg", ".jpeg", ".webp"}
from flask import request, render_template, abort, redirect, url_for
from werkzeug.utils import secure_filename
import json

import json, os

HISTORY_FILE = "communion_memory.json"
import os, json, tempfile

def load_history():
    try:
        if not os.path.exists(HISTORY_FILE):
            return []
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return []
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        # file was truncated or corrupted; start fresh but keep the bad file as backup
        try:
            os.replace(HISTORY_FILE, HISTORY_FILE + ".bad")
        except OSError:
            pass
        return []

def save_history_atomic(history):
    # write to a temp file, then rename — avoids half-written files
    d = os.path.dirname(os.path.abspath(HISTORY_FILE)) or "."
    fd, tmp = tempfile.mkstemp(prefix="hist_", dir=d, text=True)
    os.close(fd)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HISTORY_FILE)


# Load memory at startup
chat_history = load_history()

def save_history():
    save_history_atomic(chat_history)


# after ROOT/CODEX_DIR lines, add:
ASSETS_DIR = ROOT / "storage" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def _ok_json(p: Path): return p.suffix.lower() in ALLOWED_JSON
def _ok_img(p: Path):  return p.suffix.lower() in ALLOWED_IMG

IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP"]

def find_matching_image(stem: str):
    for ext in IMAGE_EXTS:
        candidate = ASSETS_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate.name  # e.g., 'braid-of-mirrors.png'
    return None
def _find_image_for(stem: str):
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        cand = ASSETS_DIR / f"{stem}{ext}"
        if cand.exists():
            return cand
    return None
# server.py

from flask import Flask, jsonify

from communion import communion_bp   # ← new

app = Flask(__name__)
app.register_blueprint(communion_bp)  # ← new


if __name__ == "__main__":
    app.run(debug=True)
    
from datetime import datetime

def _fmt_size(n: int) -> str:
    for unit in ["B","KB","MB","GB"]:
        if n < 1024.0:
            return f"{n:.0f} {unit}"
        n /= 1024.0
    return f"{n:.0f} TB"

@app.get("/library")
def library():
    rows = []
    for p in sorted(CODEX_DIR.glob("*.json")):
        stem = p.stem
        img_path = _find_image_for(stem)
        img_name = img_path.name if img_path else None

        stat = p.stat()
        rows.append({
            "filename": p.name,
            "img_name": img_name,
            "size": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "preview_url": url_for("preview_query", json=stem),
            "edit_url": url_for("edit", stem=stem),
        })

    # `index.html` loops `{% for it in items %}` and uses `all_tags`/`tag`
    return render_template("index.html", items=rows, all_tags=[], tag=None)



@app.get("/codex")
def list_codex():
    rows = []
    for p in sorted(CODEX_DIR.glob("*.json")):
        stem = p.stem
        img = find_matching_image(stem)
        rows.append({
            "name": p.name,
            "image": img,  # None if not found
            "size": p.stat().st_size,
            "mtime": p.stat().st_mtime,
        })
    return jsonify(rows)

@app.get("/codex/<path:filename>")
def fetch_codex(filename: str):
    p = CODEX_DIR / filename
    if not p.exists() or p.is_dir():
        abort(404)
    if p.suffix.lower() == ".json":
        return send_from_directory(CODEX_DIR, filename)
    abort(404)

@app.get("/assets/<path:filename>")
def fetch_asset(filename: str):
    p = ASSETS_DIR / filename
    if not p.exists() or p.is_dir():
        abort(404)
    return send_from_directory(ASSETS_DIR, filename)

# ---------- preview helpers ----------
IMG_EXTS = [".png", ".jpg", ".jpeg", ".webp"]

def find_image_for_stem(stem: str):
    for ext in IMG_EXTS:
        p = ASSETS_DIR / f"{stem}{ext}"
        if p.exists():
            return p.name
    return None

def read_json_text(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # pretty-print for the template
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        try:
            # If it’s not valid JSON, show raw text
            return path.read_text(encoding="utf-8")
        except Exception:
            return None

# /preview/<stem> — tries stem.json + stem.(png|jpg|jpeg|webp)
@app.get("/preview/<path:stem>")
def preview_by_stem(stem: str):
    json_path = CODEX_DIR / f"{stem}.json"
    img_name = find_image_for_stem(stem)
    json_text = read_json_text(json_path)
    img_url = f"/assets/{img_name}" if img_name else None
    if not json_text and not img_name:
        abort(404)
    return render_template(
        "preview.html",
        title="Living Parchment",
        stem=stem,
        json_data=json_text,
        img_url=img_url,
    )
def _write_json(stem: str, data: dict) -> None:
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(CODEX_DIR / f"{stem}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# /preview?json=<file.json>&img=<file.png> — explicit pairing
@app.post("/upload")
def upload():
    codex_file = request.files.get("codex")
    image_file = request.files.get("image")

    saved = {}
    codex_stem = None

    # Save codex (.json)
    if codex_file and codex_file.filename:
        name = secure_filename(codex_file.filename)
        if not name.lower().endswith(".json"):
            return jsonify(error="Codex must be a .json"), 400
        target = CODEX_DIR / name
        codex_file.save(target)
        saved["codex"] = target.name
        codex_stem = target.stem

    # Save image (png/jpg/jpeg/webp)
    if image_file and image_file.filename:
        name = secure_filename(image_file.filename)
        p = Path(name)
        ext = p.suffix.lower()
        if ext not in ALLOWED_IMG:
            return jsonify(error="Unsupported image type"), 400

        # if a codex was uploaded with it, rename image to match its stem
        if codex_stem:
            name = codex_stem + (".png" if ext != ".png" else ext)

        (ASSETS_DIR / name).parent.mkdir(parents=True, exist_ok=True)
        image_file.save(ASSETS_DIR / name)
        saved["image"] = name

    # If we saved a codex, bounce to its preview
    if codex_stem:
        return redirect(url_for("preview_query", json=codex_stem))

    # Otherwise just report what we saved
    return jsonify(saved)
  

@app.get("/edit/<stem>")
def edit(stem: str):
    data = read_json_text(stem)
    return render_template("edit.html", stem=stem, data=json.dumps(data, ensure_ascii=False, indent=2))

@app.post("/save/<stem>")
def save(stem: str):
    # accepts either form `content` or raw JSON body
    if request.is_json:
        content = request.get_json()
        # if posted as dict, persist directly
        if isinstance(content, dict):
            _write_json(stem, content)
        else:
            _write_json(stem, json.loads(content))
    else:
        raw = request.form.get("content", "")
        _write_json(stem, json.loads(raw))
    return redirect(url_for("preview", json=stem))

    saved = {}
from PIL import Image, ImageDraw, ImageFont

def _safe_palette(d: dict) -> tuple[str, str]:
    try:
        pal = d.get("design", {}).get("palette", [])
        bg = pal[0] if pal else "#0b1020"
        fg = "#ffffff" if len(pal) < 2 else pal[2] if len(pal) >= 3 else "#e9eeff"
        return bg, fg
    except Exception:
        return "#0b1020", "#e9eeff"

@app.post("/generate/<stem>")
def generate(stem: str):
    data = read_json_text(stem)
    title = data.get("title", stem.replace("_", " ").title())
    phase = data.get("phase", "")
    body  = data.get("body","")

    bg_hex, fg_hex = _safe_palette(data)

    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), bg_hex)
    draw = ImageDraw.Draw(img)

    # try a system font fallback
    try:
        f_title = ImageFont.truetype("arial.ttf", 56)
        f_phase = ImageFont.truetype("arial.ttf", 28)
        f_body  = ImageFont.truetype("arial.ttf", 26)
    except:
        f_title = ImageFont.load_default()
        f_phase = ImageFont.load_default()
        f_body  = ImageFont.load_default()

    # frame
    frame = 36
    draw.rectangle([frame, frame, W-frame, H-frame], outline=fg_hex, width=2)

    # title
    draw.text((frame+24, frame+20), title, fill=fg_hex, font=f_title)
    # phase
    if phase:
        draw.text((frame+24, frame+100), f"Phase: {phase}", fill=fg_hex, font=f_phase)
    # body (wrap lightly)
    import textwrap
    y = frame+160
    for line in textwrap.wrap(body, width=36):
        draw.text((frame+24, y), line, fill=fg_hex, font=f_body)
        y += 34

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out = ASSETS_DIR / f"{stem}.png"
    img.save(out, "PNG")

if __name__ == "__main__":
    init_db()
    print(">> Flask starting on port 5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
