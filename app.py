import os
import pickle
import sqlite3

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ── App setup ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

# ── Load ML model ──────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(BASE_DIR, "parking_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model, le_vehicle, le_day, le_purpose = pickle.load(f)

VALID_VEHICLE_TYPES = list(le_vehicle.classes_)
VALID_DAY_TYPES = list(le_day.classes_)
VALID_PURPOSES = list(le_purpose.classes_)

# ── Database helper ────────────────────────────────────────────────────────────
DB_PATH = os.path.join(BASE_DIR, "parking_system.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# ── GET /api/options  →  valid input values for the form ──────────────────────
@app.route("/api/options")
def options():
    return jsonify({
        "vehicle_types": VALID_VEHICLE_TYPES,
        "day_types": VALID_DAY_TYPES,
        "visit_purposes": VALID_PURPOSES,
        "entry_hour_range": [8, 22],
    })


# ── POST /api/park  →  predict + allocate slot ────────────────────────────────
@app.route("/api/park", methods=["POST"])
def park():
    data = request.get_json(force=True)

    vehicle_type = data.get("vehicle_type", "").strip()
    day_type = data.get("day_type", "").strip()
    visit_purpose = data.get("visit_purpose", "").strip()
    try:
        entry_hour = int(data.get("entry_hour", 12))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "entry_hour must be an integer"}), 400

    # Validate
    errors = []
    if vehicle_type not in VALID_VEHICLE_TYPES:
        errors.append(f"vehicle_type must be one of {VALID_VEHICLE_TYPES}")
    if day_type not in VALID_DAY_TYPES:
        errors.append(f"day_type must be one of {VALID_DAY_TYPES}")
    if visit_purpose not in VALID_PURPOSES:
        errors.append(f"visit_purpose must be one of {VALID_PURPOSES}")
    if not (8 <= entry_hour <= 22):
        errors.append("entry_hour must be between 8 and 22")
    if errors:
        return jsonify({"success": False, "error": "; ".join(errors)}), 400

    # Encode inputs
    v_enc = le_vehicle.transform([vehicle_type])[0]
    d_enc = le_day.transform([day_type])[0]
    p_enc = le_purpose.transform([visit_purpose])[0]

    input_df = pd.DataFrame([{
        "vehicle_type": v_enc,
        "entry_hour": entry_hour,
        "day_type": d_enc,
        "visit_purpose": p_enc,
    }])

    # Predict duration
    predicted_duration = float(model.predict(input_df)[0])

    # Determine zone
    if predicted_duration < 2:
        zone = "Near"
    elif predicted_duration <= 4:
        zone = "Middle"
    else:
        zone = "Far"

    # Determine slot size
    size_map = {"SUV": "Large", "Sedan": "Medium", "Hatchback": "Small"}
    slot_size = size_map[vehicle_type]

    # Find & allocate a slot
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT slot_id, floor FROM parking_slots
        WHERE slot_size = ? AND zone = ? AND is_available = 1
        LIMIT 1
        """,
        (slot_size, zone),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({
            "success": False,
            "error": f"No {slot_size} slot available in the {zone} zone.",
            "predicted_duration": round(predicted_duration, 2),
            "zone": zone,
            "slot_size": slot_size,
        }), 200

    assigned_slot = row["slot_id"]
    floor = row["floor"]

    cursor.execute(
        "UPDATE parking_slots SET is_available = 0 WHERE slot_id = ?",
        (assigned_slot,),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "predicted_duration": round(predicted_duration, 2),
        "zone": zone,
        "slot_size": slot_size,
        "assigned_slot": assigned_slot,
        "floor": floor,
    })


# ── GET /api/slots  →  all slots with status ──────────────────────────────────
@app.route("/api/slots")
def slots():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT slot_id, floor, slot_size, zone, is_available FROM parking_slots ORDER BY slot_id")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── GET /api/slots/stats  →  summary statistics ───────────────────────────────
@app.route("/api/slots/stats")
def stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM parking_slots")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS available FROM parking_slots WHERE is_available = 1")
    available = cursor.fetchone()["available"]

    # By floor
    cursor.execute("""
        SELECT floor,
               COUNT(*) AS total,
               SUM(is_available) AS available
        FROM parking_slots GROUP BY floor ORDER BY floor
    """)
    by_floor = [dict(r) for r in cursor.fetchall()]

    # By zone
    cursor.execute("""
        SELECT zone,
               COUNT(*) AS total,
               SUM(is_available) AS available
        FROM parking_slots GROUP BY zone
    """)
    by_zone = [dict(r) for r in cursor.fetchall()]

    # By size
    cursor.execute("""
        SELECT slot_size,
               COUNT(*) AS total,
               SUM(is_available) AS available
        FROM parking_slots GROUP BY slot_size
    """)
    by_size = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "total": total,
        "available": available,
        "occupied": total - available,
        "by_floor": by_floor,
        "by_zone": by_zone,
        "by_size": by_size,
    })


# ── POST /api/release/<slot_id>  →  free a specific slot ──────────────────────
@app.route("/api/release/<slot_id>", methods=["POST"])
def release(slot_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT slot_id, is_available FROM parking_slots WHERE slot_id = ?", (slot_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "error": f"Slot {slot_id} not found"}), 404

    if row["is_available"] == 1:
        conn.close()
        return jsonify({"success": False, "error": f"Slot {slot_id} is already available"}), 400

    cursor.execute("UPDATE parking_slots SET is_available = 1 WHERE slot_id = ?", (slot_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "slot_id": slot_id})


# ── POST /api/reset  →  reset all slots to available ─────────────────────────
@app.route("/api/reset", methods=["POST"])
def reset():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE parking_slots SET is_available = 1")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "All slots have been reset to available."})


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(STATIC_DIR, exist_ok=True)
    print("Smart Parking API running -> http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
