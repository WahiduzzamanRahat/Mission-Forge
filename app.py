import html
import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

# Load variables from the .env file
load_dotenv()

app = Flask(__name__)

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MISSIONS = {
    "moon": {
        "name": "Lunar Research Mission",
        "destination": "Moon",
        "min_power": 50,
        "min_comms": 55,
        "base_mass": 4.0,
        "base_budget": 260,
        "base_science": 30,
        "base_reliability": 86,
    },
    "mars": {
        "name": "Mars Exploration Mission",
        "destination": "Mars",
        "min_power": 62,
        "min_comms": 70,
        "base_mass": 5.5,
        "base_budget": 360,
        "base_science": 38,
        "base_reliability": 80,
    },
}

ROCKETS = {
    "light": {
        "name": "Light", "capacity": 8, "budget": 500,
        "power": 72, "reliability": 76, "comms": 66,
    },
    "medium": {
        "name": "Medium", "capacity": 15, "budget": 900,
        "power": 88, "reliability": 87, "comms": 82,
    },
    "heavy": {
        "name": "Heavy", "capacity": 25, "budget": 1400,
        "power": 100, "reliability": 94, "comms": 94,
    },
}

INSTRUMENTS = {
    "camera": {
        "name": "Camera", "mass": 1.0, "cost": 45,
        "power": 5, "science": 13, "risk": 1,
    },
    "spectrometer": {
        "name": "Spectrometer", "mass": 2.0, "cost": 105,
        "power": 11, "science": 25, "risk": 3,
    },
    "radiation": {
        "name": "Radiation Detector", "mass": 1.5, "cost": 85,
        "power": 8, "science": 18, "risk": 2,
    },
    "soil": {
        "name": "Soil Analyzer", "mass": 2.0, "cost": 110,
        "power": 12, "science": 24, "risk": 4,
    },
    "weather": {
        "name": "Weather Station", "mass": 1.2, "cost": 70,
        "power": 9, "science": 16, "risk": 2,
    },
}

OBJECTIVES = {
    "science": {"name": "Scientific Research", "science": 12, "risk": 3},
    "exploration": {"name": "Exploration", "science": 8, "risk": 1},
    "technology": {"name": "Technology Demonstration", "science": 6, "risk": 0},
}


def calculate_mission(payload):
    destination = payload.get("destination", "mars")
    rocket_id = payload.get("rocket", "medium")
    objective_id = payload.get("objective", "science")
    selected = payload.get("instruments", [])

    mission = MISSIONS.get(destination, MISSIONS["mars"])
    rocket = ROCKETS.get(rocket_id, ROCKETS["medium"])
    objective = OBJECTIVES.get(objective_id, OBJECTIVES["science"])

    mass = mission["base_mass"]
    budget = mission["base_budget"]
    power = rocket["power"]
    comms = rocket["comms"]
    science = mission["base_science"] + objective["science"]
    reliability = rocket["reliability"]
    risk = max(0, 18 - (reliability - 70) // 3) + objective["risk"]

    for item_id in selected:
        item = INSTRUMENTS.get(item_id)
        if not item:
            continue
        mass += item["mass"]
        budget += item["cost"]
        power -= item["power"]
        science += item["science"]
        risk += item["risk"]

    # Simplified educational model; this is NOT NASA flight software.
    mass_margin = max(
        0, min(100, (rocket["capacity"] - mass) / rocket["capacity"] * 100)
    )
    budget_margin = max(
        0, min(100, (rocket["budget"] - budget) / rocket["budget"] * 100)
    )
    power_score = max(0, min(100, power))
    comms_score = max(0, min(100, comms))
    science_score = max(0, min(100, science))
    reliability_score = max(0, min(100, reliability))

    score = (
        science_score * 0.25
        + reliability_score * 0.25
        + comms_score * 0.15
        + power_score * 0.15
        + budget_margin * 0.10
        + mass_margin * 0.10
    )

    failures = []
    if mass > rocket["capacity"]:
        failures.append("MASS LIMIT EXCEEDED")
    if budget > rocket["budget"]:
        failures.append("BUDGET EXCEEDED")
    if power < mission["min_power"]:
        failures.append("INSUFFICIENT POWER")
    if comms < mission["min_comms"]:
        failures.append("COMMUNICATION MARGIN TOO LOW")

    if mass > rocket["capacity"] * 0.90:
        risk += 7
    if power < mission["min_power"] + 8:
        risk += 7
    risk = min(100, max(0, risk))

    score = max(0, min(100, round(score - risk * 0.12)))
    success = len(failures) == 0 and score >= 55

    if not success and not failures:
        failures.append("MISSION MARGIN TOO LOW")

    return {
        "destination": mission["destination"],
        "mission_name": mission["name"],
        "rocket": rocket["name"],
        "rocket_capacity": rocket["capacity"],
        "rocket_budget": rocket["budget"],
        "mass": round(mass, 1),
        "budget": round(budget),
        "power": round(power),
        "communication": round(comms),
        "science": round(science),
        "reliability": round(reliability),
        "risk": round(risk),
        "score": score,
        "success": success,
        "failures": failures,
        "limits": {
            "mass": rocket["capacity"],
            "budget": rocket["budget"],
            "power": mission["min_power"],
            "communication": mission["min_comms"],
        },
        "selected_instruments": [
            INSTRUMENTS[i]["name"] for i in selected if i in INSTRUMENTS
        ],
        "model_note": (
            "MissionForge Educational Simulation Model — simplified for learning; "
            "not NASA flight software."
        ),
    }


@app.get("/")
def index():
    return render_template("index.html")
def _plain_text(value):
    """Extract clean text from either plain strings or WordPress rendered fields."""
    if isinstance(value, dict):
        value = value.get("rendered", "")
    if isinstance(value, str):
        # Convert <br> tags to space/newlines
        value = re.sub(r'<br\s*/?>', ' ', value, flags=re.IGNORECASE)
        # Strip all remaining HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        # Decode HTML entities like &nbsp;, &amp;, &quot;
        value = html.unescape(value)
        return value.strip()
    return ""
def _pick_apod_record(data):
    """NASA's new APOD endpoint commonly returns a list; choose the newest item."""
    if isinstance(data, list):
        if not data:
            raise ValueError("NASA returned an empty APOD list.")
        data = data[0]
    if not isinstance(data, dict):
        raise ValueError("NASA returned an unexpected APOD response format.")
    return data


def _find_image_url(data):
    """Return an actual media URL, not the NASA article/permalink URL."""
    for key in ("hdurl", "image_url", "image", "featured_image", "thumbnail"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("https://", "http://")):
            return value

    # The legacy APOD endpoint uses `url` for the media itself. On the new
    # WordPress endpoint, `url` may instead be an article page, so use it only
    # when it looks like a media file.
    value = data.get("url")
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        lower = value.lower().split("?", 1)[0]
        if any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm")):
            return value

    embedded = data.get("_embedded")
    if isinstance(embedded, dict):
        media_groups = embedded.get("wp:featuredmedia", [])
        if isinstance(media_groups, list):
            for media in media_groups:
                if not isinstance(media, dict):
                    continue
                value = media.get("source_url")
                if isinstance(value, str) and value.startswith(("https://", "http://")):
                    return value
    return ""

@app.get("/api/nasa/apod")
def nasa_apod():
    """Get APOD from NASA's new endpoint, with the legacy API as a fallback."""
    errors = []
    records = []

    # Current NASA APOD endpoint: no key required; normally returns a list.
    try:
        response = requests.get(
            "https://science.nasa.gov/wp-json/wp/v2/apod-basic",
            timeout=15,
            headers={"Accept": "application/json", "User-Agent": "MissionForge/1.0"},
        )
        response.raise_for_status()
        records.append(("new", response.json()))
    except Exception as exc:
        errors.append(f"new endpoint ({type(exc).__name__}: {exc})")

    # Fallback for temporary outages of the new endpoint.
    try:
        response = requests.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": NASA_API_KEY or "DEMO_KEY"},
            timeout=15,
            headers={"Accept": "application/json", "User-Agent": "MissionForge/1.0"},
        )
        response.raise_for_status()
        records.append(("legacy", response.json()))
    except Exception as exc:
        errors.append(f"legacy endpoint ({type(exc).__name__}: {exc})")

    for source, raw_data in records:
        try:
            data = _pick_apod_record(raw_data)
            title = _plain_text(data.get("title")) or "NASA Astronomy Picture of the Day"
            explanation = (
                _plain_text(data.get("explanation"))
                or _plain_text(data.get("excerpt"))
                or _plain_text(data.get("content"))
            )
            image_url = _find_image_url(data)
            media_type = data.get("media_type", "image")
            if not isinstance(media_type, str):
                media_type = "image"
            record_date = data.get("date", "")
            if isinstance(record_date, str) and "T" in record_date:
                record_date = record_date.split("T", 1)[0]

            if not title or (not image_url and media_type == "image"):
                raise ValueError("NASA response is missing a title or image URL.")

            return jsonify({
                "ok": True,
                "title": title,
                "date": record_date,
                "explanation": explanation,
                "media_type": media_type,
                "url": image_url,
                "hdurl": image_url,
                "copyright": _plain_text(data.get("copyright")) or _plain_text(data.get("credit")),
                "source": "NASA APOD API",
            })
        except Exception as exc:
            errors.append(f"{source} processing ({type(exc).__name__}: {exc})")

    return jsonify({
        "ok": False,
        "message": "NASA's picture service is temporarily unavailable. MissionForge's mission planner still works.",
        "detail": "; ".join(errors) or "No usable NASA APOD response was received.",
    }), 503
def local_advisor(result):
    advice = []
    if result["mass"] > result["limits"]["mass"]:
        advice.append(
            "Reduce payload mass or select a higher-capacity launch vehicle."
        )
    if result["power"] < result["limits"]["power"]:
        advice.append(
            "Remove a high-power instrument or improve the power margin."
        )
    if result["budget"] > result["limits"]["budget"]:
        advice.append(
            "Reduce payload cost or select a launch vehicle with a larger budget envelope."
        )
    if result["communication"] < result["limits"]["communication"]:
        advice.append(
            "Improve the communications architecture or use a more capable vehicle."
        )

    if not advice:
        if result["risk"] > 35:
            advice.append(
                "Your mission is feasible, but the margins are tight. "
                "Consider removing one optional instrument."
            )
        else:
            advice.append(
                "Your mission has healthy margins. Consider a What-If experiment "
                "to explore the trade-offs."
            )

    strongest = max(
        [
            ("Scientific value", result["science"]),
            ("Reliability", result["reliability"]),
            ("Power", result["power"]),
            ("Communication", result["communication"]),
        ],
        key=lambda item: item[1],
    )[0]

    return {
        "summary": (
            f"Your mission scores {result['score']}/100 in the "
            "MissionForge educational model."
        ),
        "strongest": strongest,
        "risk": (
            " ; ".join(result["failures"])
            if result["failures"]
            else (
                "Power and payload margins are the main areas to watch."
                if result["risk"] > 30
                else "No critical constraint is currently violated."
            )
        ),
        "recommendations": advice[:2],
        "source": "MissionForge rule-based advisor (works without an AI key).",
    }


@app.post("/api/advisor")
def advisor():
    payload = request.get_json(silent=True) or {}
    result = calculate_mission(payload)

    if not GEMINI_API_KEY:
        return jsonify(local_advisor(result))

    prompt = f"""
You are the AI Mission Advisor inside an educational space-mission design game.
Do not claim these calculations are NASA flight software. Explain the supplied
MissionForge Educational Simulation Model in simple language for students.

Mission:
Destination: {result['destination']}
Launch vehicle: {result['rocket']}
Mass: {result['mass']} / {result['limits']['mass']} tons
Budget: ${result['budget']}M / ${result['limits']['budget']}M
Power: {result['power']} / minimum {result['limits']['power']}
Communication: {result['communication']} / minimum {result['limits']['communication']}
Scientific value: {result['science']}
Reliability: {result['reliability']}
Risk: {result['risk']}
Score: {result['score']}
Failures: {result['failures']}
Instruments: {result['selected_instruments']}

Return exactly four short sections:
STRONGEST:
RISK:
RECOMMENDATION 1:
RECOMMENDATION 2:
"""
    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent"
        )
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        generated_text = data["candidates"][0]["content"]["parts"][0]["text"]

        return jsonify({
            "summary": (
                f"AI analysis for a {result['destination']} mission "
                f"scoring {result['score']}/100."
            ),
            "text": generated_text,
            "source": f"Gemini ({GEMINI_MODEL})",
        })
    except Exception:
        return jsonify(
            local_advisor(result)
            | {
                "source": (
                    "MissionForge fallback advisor (Gemini was unavailable)."
                )
            }
        )


@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    return jsonify(calculate_mission(payload))


@app.get("/api/config")
def config():
    return jsonify({
        "missions": MISSIONS,
        "rockets": ROCKETS,
        "instruments": INSTRUMENTS,
        "objectives": OBJECTIVES,
        "gemini_enabled": bool(GEMINI_API_KEY),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True,
    )
