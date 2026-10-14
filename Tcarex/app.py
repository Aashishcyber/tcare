from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
import random
import base64
import io
import re

app = Flask(__name__)
CORS(app)

DB_FILE = 'database.json'
TXT_FILE = 'appointment.txt'

INITIAL_DB = {
    "doctors_accounts": [],
    "pending_requests": [],
    "confirmed_appointments": [],
    "emergency_alerts": [],
    "doctors_list": [
        {
            "name": "Dr. Aris",
            "specialty": "Cardiologist (Heart)",
            "keywords": ["heart", "chest", "cardio"],
            "rating": 4.5,
            "total_reviews": 10,
            "fees": 700,
            "area": "Indiranagar",
            "distance_km": 3.2
        },
        {
            "name": "Dr. Miller",
            "specialty": "Cardiologist (Heart)",
            "keywords": ["heart", "chest", "cardio"],
            "rating": 4.8,
            "total_reviews": 5,
            "fees": 900,
            "area": "Koramangala",
            "distance_km": 2.1
        },
        {
            "name": "Dr. Sarah",
            "specialty": "Dermatologist (Skin)",
            "keywords": ["skin", "rash", "acne"],
            "rating": 4.7,
            "total_reviews": 12,
            "fees": 800,
            "area": "HSR Layout",
            "distance_km": 4.4
        },
        {
            "name": "Dr. Gupta",
            "specialty": "Dermatologist (Skin)",
            "keywords": ["skin", "rash", "acne"],
            "rating": 4.2,
            "total_reviews": 8,
            "fees": 600,
            "area": "BTM Layout",
            "distance_km": 5.1
        },
        {
            "name": "Dr. Khanna",
            "specialty": "Pediatrician (Kids)",
            "keywords": ["child", "baby", "kids"],
            "rating": 4.9,
            "total_reviews": 20,
            "fees": 1000,
            "area": "Jayanagar",
            "distance_km": 3.8
        },
        {
            "name": "Dr. Smith",
            "specialty": "Neurologist (Brain)",
            "keywords": ["brain", "neuro", "headache"],
            "rating": 4.6,
            "total_reviews": 15,
            "fees": 1200,
            "area": "Whitefield",
            "distance_km": 7.9
        },
        {
            "name": "Dr. Emma",
            "specialty": "Orthopedic (Bones)",
            "keywords": ["bone", "fracture", "joint"],
            "rating": 4.4,
            "total_reviews": 7,
            "fees": 750,
            "area": "Marathahalli",
            "distance_km": 6.4
        }
    ]
}

EMERGENCY_CENTERS = [
    {
        "name": "City Trauma Center",
        "type": "Trauma & Emergency",
        "area": "Koramangala",
        "distance_km": 1.8,
        "rating": 4.8,
        "phone": "+91-80-44001122",
        "open": "24x7",
        "specialties": ["accident", "trauma", "fracture", "bleeding", "road"]
    },
    {
        "name": "Metro MultiCare ER",
        "type": "General Emergency",
        "area": "Indiranagar",
        "distance_km": 2.4,
        "rating": 4.6,
        "phone": "+91-80-40009321",
        "open": "24x7",
        "specialties": ["general", "fever", "pain", "injury", "accident"]
    },
    {
        "name": "Lifeline Neuro-Cardiac ER",
        "type": "Cardiac / Neuro",
        "area": "HSR Layout",
        "distance_km": 3.1,
        "rating": 4.7,
        "phone": "+91-80-45558899",
        "open": "24x7",
        "specialties": ["cardiac", "heart", "stroke", "head", "neuro"]
    },
    {
        "name": "RapidAid Hospital",
        "type": "Accident Response",
        "area": "BTM Layout",
        "distance_km": 4.3,
        "rating": 4.5,
        "phone": "+91-80-46770011",
        "open": "24x7",
        "specialties": ["accident", "trauma", "fracture", "burn", "response"]
    }
]

db = INITIAL_DB

DEGREE_TERMS = [
    "MBBS", "MD", "MS", "DM", "MCH", "DNB", "BAMS", "BHMS",
    "MEDICAL", "UNIVERSITY", "COLLEGE", "DEGREE", "NMC", "MCI", "REGISTRATION"
]

SPECIALTY_KEYWORDS = {
    "cardio": ["heart", "chest", "cardio", "cardiac"],
    "derma": ["skin", "rash", "acne", "allergy"],
    "pedia": ["child", "baby", "kids", "fever"],
    "neuro": ["brain", "neuro", "headache", "stroke"],
    "ortho": ["bone", "fracture", "joint", "spine"],
    "gyn": ["pregnancy", "women", "gyn", "period"],
    "general": ["fever", "pain", "infection", "weakness"]
}


def _doctor_defaults(index):
    fallback_catalog = INITIAL_DB["doctors_list"]
    return fallback_catalog[index % len(fallback_catalog)]


def normalize_doctors():
    changed = False
    for i, doc in enumerate(db.get("doctors_list", [])):
        defaults = _doctor_defaults(i)
        if "fees" not in doc:
            doc["fees"] = defaults["fees"]
            changed = True
        if "area" not in doc:
            doc["area"] = defaults["area"]
            changed = True
        if "distance_km" not in doc:
            doc["distance_km"] = defaults["distance_km"]
            changed = True
        if "total_reviews" not in doc:
            doc["total_reviews"] = defaults["total_reviews"]
            changed = True
    return changed


def load_db():
    global db
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                db = json.load(f)
        except Exception:
            db = INITIAL_DB
    else:
        db = INITIAL_DB

    schema_changed = False
    if "emergency_alerts" not in db:
        db["emergency_alerts"] = []
        schema_changed = True

    if normalize_doctors():
        save_db()
    elif schema_changed:
        save_db()
    elif not os.path.exists(DB_FILE):
        save_db()


def save_db():
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

    with open(TXT_FILE, 'w') as f:
        f.write("=== TCAREX - APPOINTMENT RECORDS ===\n")
        f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n")
        f.write("=" * 60 + "\n\n")
        for app_data in db["confirmed_appointments"]:
            f.write(
                f"Patient: {app_data['name']} | Issue: {app_data.get('disease')} | "
                f"Doctor: {app_data['doctor']} | Time: {app_data['date']} {app_data['time']}\n"
            )
        if db.get("emergency_alerts"):
            f.write("\n" + "=" * 60 + "\n")
            f.write("Emergency Alerts\n")
            f.write("=" * 60 + "\n")
            for alert in db["emergency_alerts"][-20:]:
                f.write(
                    f"Name: {alert.get('name', '-')}"
                    f" | Incident: {alert.get('incident', '-')}"
                    f" | Center: {alert.get('assigned_center', '-')}"
                    f" | Specialist: {alert.get('recommended_specialist', '-')}"
                    f" | Location: {alert.get('lat', '-')},{alert.get('lng', '-')}"
                    f" | Time: {alert.get('created_at', '-')}\n"
                )


load_db()


def _build_keywords_from_profession(profession):
    text = (profession or "").lower()
    keywords = set()

    for token, values in SPECIALTY_KEYWORDS.items():
        if token in text:
            keywords.update(values)

    words = [w for w in re.findall(r"[a-zA-Z]+", text) if len(w) > 3]
    keywords.update(words[:4])

    if not keywords:
        keywords.update(SPECIALTY_KEYWORDS["general"])

    return sorted(keywords)


def _extract_text_from_degree_image(image_base64):
    raw = base64.b64decode(image_base64, validate=True)
    if len(raw) < 1000:
        raise ValueError("Image looks too small or invalid")

    try:
        from PIL import Image
        import pytesseract
    except Exception:
        return ""

    img = Image.open(io.BytesIO(raw))
    text = pytesseract.image_to_string(img)
    return (text or "").upper()


def _verify_degree_document(image_base64):
    raw = base64.b64decode(image_base64, validate=True)
    extracted = _extract_text_from_degree_image(image_base64)
    if not extracted:
        is_known_image = raw.startswith(b"\x89PNG") or raw.startswith(b"\xff\xd8\xff")
        size_ok = len(raw) > 30_000
        return {
            "valid": bool(is_known_image and size_ok),
            "confidence": 0.55 if (is_known_image and size_ok) else 0.2,
            "detected_terms": [],
            "reason": "OCR unavailable; used basic image quality validation"
        }

    matched = [term for term in DEGREE_TERMS if term in extracted]
    confidence = round(min(1.0, len(matched) / 5.0), 2)
    valid = len(matched) >= 2

    return {
        "valid": valid,
        "confidence": confidence,
        "detected_terms": matched,
        "preview": extracted[:220].replace("\n", " ")
    }


@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    sorted_docs = sorted(
        db["doctors_list"],
        key=lambda x: (x.get('rating', 0), -x.get('distance_km', 999)),
        reverse=True
    )
    return jsonify(sorted_docs)


@app.route('/api/chatbot/recommend', methods=['GET'])
def chatbot_recommend():
    symptoms = request.args.get('symptoms', '').strip().lower()
    doctors = db.get("doctors_list", [])

    if symptoms:
        matched = [
            d for d in doctors
            if any(k in symptoms for k in d.get('keywords', []))
        ]
    else:
        matched = doctors

    recommendations = matched if matched else doctors
    recommendations = sorted(
        recommendations,
        key=lambda d: (-d.get('rating', 0), d.get('distance_km', 999))
    )

    return jsonify({
        "symptoms": symptoms,
        "count": len(recommendations),
        "doctors": recommendations
    })


@app.route('/api/doctors/<doctor_name>', methods=['GET'])
def get_doctor_detail(doctor_name):
    query = doctor_name.strip().lower()
    doctor = next(
        (d for d in db.get("doctors_list", []) if d.get('name', '').lower() == query),
        None
    )
    if not doctor:
        return jsonify({"status": "error", "message": "Doctor not found"}), 404
    return jsonify(doctor)


@app.route('/api/emergency/nearby', methods=['GET'])
def get_nearby_emergency():
    limit = request.args.get('limit', default=4, type=int)
    sorted_centers = sorted(
        EMERGENCY_CENTERS,
        key=lambda c: (-c.get('rating', 0), c.get('distance_km', 999))
    )
    return jsonify({
        "number": "108",
        "centers": sorted_centers[:max(1, min(limit, 10))]
    })


def _emergency_specialist_from_incident(incident):
    text = (incident or "").strip().lower()
    if any(k in text for k in ["head", "brain", "stroke", "neuro"]):
        return "Neuro Specialist"
    if any(k in text for k in ["heart", "chest", "cardiac"]):
        return "Cardiac Specialist"
    if any(k in text for k in ["fracture", "bone", "spine", "ortho"]):
        return "Orthopedic Trauma Specialist"
    if any(k in text for k in ["burn", "fire"]):
        return "Burn Care Specialist"
    if any(k in text for k in ["bleed", "accident", "road", "injury", "trauma"]):
        return "Trauma Specialist"
    return "General Emergency Specialist"


def _find_best_emergency_center(incident):
    text = (incident or "").strip().lower()

    def center_score(center):
        specs = [s.lower() for s in center.get("specialties", [])]
        matched = sum(1 for s in specs if s in text)
        return (-matched, center.get("distance_km", 999), -center.get("rating", 0))

    ranked = sorted(EMERGENCY_CENTERS, key=center_score)
    return ranked[0] if ranked else None


@app.route('/api/emergency/alert', methods=['POST'])
def emergency_alert():
    data = request.get_json() or {}
    incident = (data.get("incident") or "").strip()
    name = (data.get("name") or "").strip()
    lat = data.get("lat")
    lng = data.get("lng")
    contact_name = (data.get("contact_name") or "").strip()
    contact_phone = (data.get("contact_phone") or "").strip()

    best_center = _find_best_emergency_center(incident)
    specialist = _emergency_specialist_from_incident(incident)

    alert_data = {
        "id": len(db.get("emergency_alerts", [])) + 1,
        "name": name or "Unknown",
        "incident": incident or "Not specified",
        "lat": lat,
        "lng": lng,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "recommended_specialist": specialist,
        "assigned_center": best_center.get("name") if best_center else "Not available",
        "assigned_center_phone": best_center.get("phone") if best_center else "",
        "assigned_center_area": best_center.get("area") if best_center else "",
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }

    db.setdefault("emergency_alerts", []).append(alert_data)
    save_db()

    return jsonify({
        "status": "success",
        "helpline": "108",
        "recommended_specialist": specialist,
        "nearest_center": best_center,
        "alert_id": alert_data["id"]
    })


@app.route('/api/book', methods=['POST'])
def book_appointment():
    data = request.get_json()
    data['id'] = len(db["pending_requests"]) + len(db["confirmed_appointments"]) + 1

    hour = random.randint(8, 16)
    minute = random.choice(["00", "15", "30", "45"])
    time_24h = f"{hour:02d}:{minute}"
    time_12h = datetime.strptime(time_24h, "%H:%M").strftime("%I:%M %p")

    data['time'] = time_12h
    data['status'] = "Auto-Confirmed"

    db["confirmed_appointments"].append(data)
    save_db()

    return jsonify({
        "status": "success",
        "message": f"AI Suggestion: Appointment Auto-Confirmed for {time_12h}",
        "time": time_12h
    })


@app.route('/api/doctor/login', methods=['POST'])
def login():
    data = request.get_json()
    user = next(
        (
            d for d in db["doctors_accounts"]
            if d['username'] == data.get('username') and d['password'] == data.get('password')
        ),
        None
    )
    if user:
        return jsonify({"status": "success", "doctorName": user['name']})
    return jsonify({"status": "error", "message": "Login failed"}), 401


@app.route('/api/doctor/verify-degree', methods=['POST'])
def verify_degree():
    data = request.get_json() or {}
    image_base64 = (data.get('image_base64') or '').strip()
    if not image_base64:
        return jsonify({"status": "error", "message": "Degree image is required"}), 400

    try:
        result = _verify_degree_document(image_base64)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"Verification failed: {str(exc)}"}), 400

    return jsonify({"status": "success", **result})


@app.route('/api/doctor/register', methods=['POST'])
def register_doctor():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    profession = (data.get('profession') or '').strip()
    degree_verified = bool(data.get('degree_verified'))

    if not username or not password or not name or not profession:
        return jsonify({"status": "error", "message": "Name, profession, username and password are required"}), 400
    if not degree_verified:
        return jsonify({"status": "error", "message": "Degree verification is required"}), 400

    already_exists = next(
        (d for d in db["doctors_accounts"] if d.get('username', '').lower() == username.lower()),
        None
    )
    if already_exists:
        return jsonify({"status": "error", "message": "Username already exists"}), 409

    db["doctors_accounts"].append({
        "username": username,
        "password": password,
        "name": name,
        "profession": profession,
        "degree_verified": True
    })

    display_name = name if name.lower().startswith("dr.") else f"Dr. {name}"
    exists_in_list = next(
        (d for d in db.get("doctors_list", []) if d.get('name', '').lower() == display_name.lower()),
        None
    )
    if not exists_in_list:
        db.setdefault("doctors_list", []).append({
            "name": display_name,
            "specialty": profession,
            "keywords": _build_keywords_from_profession(profession),
            "rating": 3.0,
            "total_reviews": 1,
            "fees": 700,
            "area": "City Center",
            "distance_km": 5.0
        })

    save_db()
    return jsonify({"status": "success", "message": "Doctor registered successfully"})


@app.route('/api/admin/requests', methods=['GET'])
def get_requests():
    return jsonify(db["confirmed_appointments"])


@app.route('/api/patient/status/<name>', methods=['GET'])
def get_status(name):
    query = name.strip().lower()
    results = [a for a in db["confirmed_appointments"] if query in a['name'].lower()]
    return jsonify(results[::-1])


@app.route('/api/patient/rate', methods=['POST'])
def rate_appointment():
    data = request.get_json()
    req_id = int(data.get('id'))
    rating_val = int(data.get('rating'))
    for app_item in db["confirmed_appointments"]:
        if app_item['id'] == req_id:
            app_item['rating'] = f"{rating_val} Stars"
            for doc in db["doctors_list"]:
                if doc['name'] == app_item['doctor']:
                    curr_score = doc['rating'] * doc['total_reviews']
                    doc['total_reviews'] += 1
                    doc['rating'] = round((curr_score + rating_val) / doc['total_reviews'], 1)
            break
    save_db()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
