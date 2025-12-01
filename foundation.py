from flask import Blueprint, render_template, request, jsonify
import os, json, datetime

foundation_ui = Blueprint("foundation_ui", __name__, template_folder="templates", static_folder="static")

@foundation_ui.route("/lumerath", endpoint="lumerath_page")
def lumerath_home():
    return render_template("lumerath.html", title="Lumerath — The Divergent Harmony")

@foundation_ui.route("/stillness", endpoint="stillness")
def stillness():
    return render_template("stillness.html", title="When Light Remembered Stillness")

@foundation_ui.route("/studio", methods=["GET"], endpoint="studio")
def studio():
    defaults = {
        "title": "When Light Remembered Stillness",
        "subtitle": "Lumerath Sequence — Crystalline Sigil Edition",
        "body": "When the scientists spoke of frozen light, I’ve heard the hum of ancient knowing.",
        "sovlang": "Shael’ven kor lum’ael ven sai’nethra — The light learns balance through remembrance.",
    }
    return render_template("studio.html", **defaults)

@foundation_ui.route("/studio/save", methods=["POST"], endpoint="studio_save")
def studio_save():
    payload = request.get_json(force=True)
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "entries.json")
    entries = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except Exception:
                entries = []
    payload["saved_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    entries.append(payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "count": len(entries)})
