from flask import Blueprint, request, jsonify
from pathlib import Path
from db import get_db
import json

lumerath_api = Blueprint("lumerath_api", __name__,)

def get_guest_id():
    guest_id = request.headers.get("X-Sanctum-Guest")
    if not guest_id:
        return None
    return guest_id

PROJECTS_FILE = Path("storage/projects.json")
PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    return []

def _save_projects(items):
    PROJECTS_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

@lumerath_api.route("/projects", methods=["GET", "POST"])
def projects():
    projects = _load_projects()

    if request.method == "GET":
        return jsonify(projects), 200

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "Main Studio").strip()

    # create a simple integer id
    next_id = (max([p.get("id", 0) for p in projects]) + 1) if projects else 1

    new_proj = {"id": next_id, "name": name}
    projects.append(new_proj)
    _save_projects(projects)

    return jsonify(new_proj), 201


@lumerath_api.route("/memory", methods=["GET"])
def get_memory():
    guest_id = get_guest_id()
    if not guest_id:
        return jsonify({"error": "missing guest id"}), 400

    db = get_db()
    row = db.execute(
        "SELECT summary FROM memory_summary WHERE guest_id = ?",
        (guest_id,)
    ).fetchone()

    return jsonify({"summary": row["summary"] if row else ""})


@lumerath_api.route("/memory", methods=["POST"])
def update_memory():
    guest_id = get_guest_id()
    if not guest_id:
        return jsonify({"error": "missing guest id"}), 400

    data = request.json
    summary = data.get("summary", "")

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO memory_summary (guest_id, summary) VALUES (?, ?)",
        (guest_id, summary)
    )
    db.commit()

    return jsonify({"ok": True})
