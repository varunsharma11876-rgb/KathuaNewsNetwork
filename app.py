from flask import Flask, jsonify, render_template, abort
from dotenv import load_dotenv
from pathlib import Path
import requests
import os

app = Flask(__name__)

# Load API credentials securely
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

FOOTBALL_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

channels = [
    {"id": 1, "name": "Live Cricket", "category": "Cricket",
     "description": "Cricket news, matches and highlights"},
    {"id": 2, "name": "Live Football", "category": "Soccer",
     "description": "Football matches and updates"},
    {"id": 3, "name": "Kathua News", "category": "Local News",
     "description": "News from Kathua and surrounding areas"},
    {"id": 4, "name": "Jammu News", "category": "Regional News",
     "description": "News from Jammu and Kashmir"},
    {"id": 5, "name": "India News", "category": "National News",
     "description": "Latest national news"},
    {"id": 6, "name": "Sports Highlights", "category": "Sports",
     "description": "Cricket and football highlights"}
]


@app.route("/")
def home():
    return render_template("index.html", channels=channels)


@app.route("/api/channels")
def channel_list():
    return jsonify(channels)


@app.route("/api/scores")
def scores():
    if not FOOTBALL_TOKEN:
        return jsonify({
            "status": "configuration_error",
            "message": "Football API token is missing.",
            "matches": []
        }), 503

    try:
        response = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": FOOTBALL_TOKEN},
            params={"status": "LIVE"},
            timeout=20
        )

        if response.status_code != 200:
            return jsonify({
                "status": "provider_error",
                "http_status": response.status_code,
                "message": "Football score provider returned an error.",
                "matches": []
            }), 502

        data = response.json()

        matches = []

        for match in data.get("matches", []):
            score = match.get("score", {})
            full_time = score.get("fullTime", {})

            matches.append({
                "competition": match.get("competition", {}).get("name"),
                "home_team": match.get("homeTeam", {}).get("name"),
                "away_team": match.get("awayTeam", {}).get("name"),
                "home_score": full_time.get("home"),
                "away_score": full_time.get("away"),
                "status": match.get("status"),
                "utc_date": match.get("utcDate")
            })

        return jsonify({
            "status": "success" if matches else "no_live_matches",
            "provider": "Football-Data.org",
            "count": len(matches),
            "matches": matches,
            "message": (
                "Live football matches retrieved."
                if matches else
                "No live football matches are available right now."
            )
        })

    except requests.RequestException:
        return jsonify({
            "status": "connection_error",
            "message": "Could not connect to football provider.",
            "matches": []
        }), 503


@app.route("/watch/<int:channel_id>")
def watch(channel_id):
    channel = next(
        (c for c in channels if c["id"] == channel_id), None
    )

    if channel is None:
        abort(404)

    return render_template("watch.html", channel=channel)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
