# MissionForge 🚀

**Design. Balance. Launch. Survive.**

MissionForge is an educational space-mission design simulator inspired by the NASA Space Apps Challenge **Space Mission Design Game** challenge.

It lets users:

- Choose Moon or Mars
- Choose a mission objective
- Select a launch vehicle
- Select scientific instruments
- Balance mass, budget, power, communications, science and risk
- Run a mission simulation
- Explore What-If trade-offs
- Get an AI Mission Advisor analysis
- Display NASA Astronomy Picture of the Day data

## Important scientific note

MissionForge uses a simplified **MissionForge Educational Simulation Model** for demonstration and learning. It is **not NASA flight-analysis software**, and its numerical scoring should not be interpreted as a real mission-planning result.

## Run locally

### 1. Install Python

Python 3.10+ recommended.

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Configure keys

Copy `.env.example` to `.env`.

```text
NASA_API_KEY=DEMO_KEY
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

NASA key:
https://api.nasa.gov/

Gemini key:
https://aistudio.google.com/app/apikey

The project works without a Gemini key because it contains a deterministic fallback Mission Advisor.

### 5. Start

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Project structure

```text
MissionForge/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```

## Hackathon demo flow

1. Start a Mars mission.
2. Select a medium launch vehicle.
3. Add several instruments.
4. Show telemetry changing.
5. Deliberately create a constraint violation.
6. Remove an instrument or change the launch vehicle.
7. Run the mission.
8. Show the score and AI Mission Advisor.
9. Use What-If Lab to demonstrate trade-offs.
10. Show NASA open data at the bottom of the report.

## Suggested pitch

> MissionForge turns space-mission systems engineering into an interactive learning experience. Players discover that every scientific decision creates engineering trade-offs across mass, power, budget, communication and risk.

## Security

Never commit `.env` or API keys to GitHub.
