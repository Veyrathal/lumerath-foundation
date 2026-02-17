from flask import Blueprint, request, jsonify
from db import get_db
import json

lumerath_api = Blueprint("lumerath_api", __name__,)

def get_guest_id():
    guest_id = request.headers.get("X-Sanctum-Guest")
    if not guest_id:
        return None
    return guest_id


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
