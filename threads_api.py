# threads_api.py
import os, hashlib, time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import imagehash
import json, time, sqlite3
from db import get_db

bp = Blueprint("threads", __name__, url_prefix="/api")


UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- In-memory store (swap to SQLite later) ---
THREADS = {}   # {thread_id: {"title":..., "location":..., "year":..., "notes":..., "posts":[post_ids]}}
POSTS = {}     # {post_id: {"thread_id":..., "author":"user", "text":..., "assets":[{url,hash,exif}]}}
 
def _save_image(file_storage):
    fn = secure_filename(file_storage.filename or f"img_{int(time.time()*1000)}.jpg")
    path = os.path.join(UPLOAD_DIR, fn)
    file_storage.save(path)

    # Web copy (ensure reasonable size)
    try:
        im = Image.open(path)
        im.thumbnail((1920, 1920))
        im.save(path, quality=88, optimize=True)
    except Exception:
        pass

    # sha256 for integrity
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    # EXIF (best-effort)
    exif = {}
    # Perceptual hash for “same building, different crop” matching
    try:
    im = Image.open(path)
    phash = str(imagehash.phash(im))
    except Exception:
    phash = None
    try:
        exif_raw = Image.open(path)._getexif() or {}
        for k,v in exif_raw.items():
            tag = ExifTags.TAGS.get(k, str(k))
            exif[tag] = v
    except Exception:
        pass
        
        return {"url": f"/{path}", "hash": digest, "phash": phash, "exif": exif}
    return {"url": f"/{path}", "hash": digest, "exif": exif}

@bp.post("/threads")
def create_thread():
    data = request.json or {}
    tid = str(int(time.time()*1000))
    THREADS[tid] = {
        "title": data.get("title","Untitled"),
        "location": data.get("location"),
        "year": data.get("year"),
        "notes": data.get("notes"),
        "posts": []
    }
    conn = get_db(); cur = conn.cursor()
    cur.execute("""INSERT INTO threads(id,title,location,year,notes,created_at)
                   VALUES(?,?,?,?,?,?)""",
                (tid, data.get("title","Untitled"),
                 data.get("location"), data.get("year"),
                 data.get("notes"), int(time.time())))
    conn.commit(); conn.close()
    return jsonify({"thread_id": tid, "thread": THREADS[tid]})

@bp.post("/threads/<tid>/post")
def add_post(tid):
    text = request.form.get("text","").strip()
    pid  = str(int(time.time()*1000))

    # ensure thread exists
    conn = get_db(); cur = conn.cursor()
    t = cur.execute("SELECT id FROM threads WHERE id=?", (tid,)).fetchone()
    if not t: 
        conn.close(); return jsonify({"error":"thread not found"}), 404

    cur.execute("""INSERT INTO posts(id,thread_id,author,text,created_at)
                   VALUES(?,?,?,?,?)""",
                (pid, tid, "user", text, int(time.time())))

    assets = []
    for f in request.files.getlist("images"):
        meta = _save_image(f)  # returns {url, hash, exif}
        aid = f"{pid}_{len(assets)}"
        cur.execute("""INSERT INTO assets(id,post_id,url,sha256,exif_json)
                       VALUES(?,?,?,?,?)""",
                    (aid, pid, meta["url"], meta["hash"], json.dumps(meta["exif"])))
        assets.append(meta)

    conn.commit(); conn.close()
    return jsonify({"post_id": pid,
                    "post": {"thread_id": tid, "author":"user", "text": text, "assets": assets}})

@bp.get("/threads/<tid>")
def get_thread(tid):
    conn = get_db(); cur = conn.cursor()
    th = cur.execute("SELECT * FROM threads WHERE id=?", (tid,)).fetchone()
    if not th: 
        conn.close(); return jsonify({"error":"thread not found"}), 404

    posts = cur.execute("SELECT * FROM posts WHERE thread_id=? ORDER BY created_at", (tid,)).fetchall()
    out_posts = []
    for p in posts:
        a = cur.execute("SELECT url,sha256,exif_json FROM assets WHERE post_id=?", (p["id"],)).fetchall()
        out_posts.append({
            "thread_id": tid,
            "author": p["author"],
            "text": p["text"],
            "assets": [{"url": r["url"], "hash": r["sha256"], "exif": json.loads(r["exif_json"] or "{}")} for r in a]
        })
    conn.close()
    return jsonify({"thread": dict(th), "posts": out_posts})

@bp.post("/threads/<tid>/promote")
def promote(tid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE threads SET promoted=1 WHERE id=?", (tid,))
    if cur.rowcount == 0:
        conn.close(); return jsonify({"error":"thread not found"}), 404
    conn.commit(); conn.close()
    return jsonify({"ok": True})

@bp.get("/threads/<tid>/continuity")
def continuity(tid):
    conn = get_db(); cur = conn.cursor()

    # hashes in this thread
    hashes = [r["sha256"] for r in cur.execute("""
        SELECT a.sha256
        FROM assets a
        JOIN posts p ON p.id=a.post_id
        WHERE p.thread_id=?
        GROUP BY a.sha256
    """, (tid,)).fetchall()]

    matches = []
    for h in hashes:
        rows = cur.execute("""
          SELECT t.id AS thread_id, t.title, p.id AS post_id, a.url, a.sha256
          FROM assets a
          JOIN posts p ON p.id=a.post_id
          JOIN threads t ON t.id=p.thread_id
          WHERE a.sha256=? AND t.id<>?
          ORDER BY t.created_at
        """, (h, tid)).fetchall()
        if rows:
            matches.append({"hash": h, "occurrences": [dict(r) for r in rows]})

    conn.close()
    return jsonify({"hashes_checked": len(hashes), "chains": matches})
