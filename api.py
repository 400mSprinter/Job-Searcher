# Created: 2026-03-11 10:30
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

from db import init_db
from reminders import get_reminders
from tracker import (
    VALID_STATUSES,
    add_application,
    delete_application,
    get_application,
    list_applications,
    update_application,
)
from espresso.espresso_db import init_espresso_db
from espresso.espresso_tracker import (
    add_shot, update_shot, get_shot, list_shots, delete_shot,
    get_distinct_beans, get_distinct_equipment,
)
from espresso.espresso_stats import get_stats as get_espresso_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_espresso_db()
    yield


app = FastAPI(title="Job Search Dashboard", lifespan=lifespan)


def row_to_dict(row):
    return dict(row) if row else None


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/chess", StaticFiles(directory="chess", html=True), name="chess")


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


# --- Applications CRUD ---

@app.get("/api/applications")
def api_list(status: str | None = None):
    apps = list_applications(status)
    return [row_to_dict(a) for a in apps]


@app.get("/api/applications/{id}")
def api_get(id: int):
    app = get_application(id)
    if not app:
        raise HTTPException(status_code=404, detail="Not found")
    return row_to_dict(app)


class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: str = "Applied"
    date_applied: str | None = None
    notes: str | None = None
    url: str | None = None
    contact: str | None = None
    follow_up_date: str | None = None


@app.post("/api/applications", status_code=201)
def api_add(body: ApplicationCreate):
    new_id = add_application(**body.model_dump())
    return {"id": new_id}


class ApplicationUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    status: str | None = None
    notes: str | None = None
    url: str | None = None
    contact: str | None = None
    follow_up_date: str | None = None


@app.patch("/api/applications/{id}")
def api_update(id: int, body: ApplicationUpdate):
    if not get_application(id):
        raise HTTPException(status_code=404, detail="Not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if fields:
        update_application(id, **fields)
    return row_to_dict(get_application(id))


@app.delete("/api/applications/{id}", status_code=204)
def api_delete(id: int):
    if not get_application(id):
        raise HTTPException(status_code=404, detail="Not found")
    delete_application(id)


# --- Reminders ---

@app.get("/api/reminders")
def api_reminders():
    items = get_reminders()
    return [{"application": row_to_dict(a), "reason": reason} for a, reason in items]


# --- Valid statuses ---

@app.get("/api/statuses")
def api_statuses():
    return VALID_STATUSES

# --- Greenhouse Job Discovery ---

GREENHOUSE_COMPANIES = [
    {"name": "Coinbase",          "token": "coinbase"},
    {"name": "Ripple",            "token": "ripple"},
    {"name": "Chainalysis",       "token": "chainalysis"},
    {"name": "Circle",            "token": "circle"},
    {"name": "Fireblocks",        "token": "fireblocks"},
    {"name": "Galaxy Digital",    "token": "galaxy"},
    {"name": "Kraken",            "token": "kraken"},
    {"name": "KKR",               "token": "kkr"},
    {"name": "Gemini",            "token": "gemini"},
    {"name": "FalconX",           "token": "falconx"},
    {"name": "BitGo",             "token": "bitgo"},
    {"name": "Jump Crypto",       "token": "jumpcrypto"},
    {"name": "GSR",               "token": "gsrmarkets"},
    {"name": "Jane Street",       "token": "janestreet"},
    {"name": "Copper.co",         "token": "copperco"},
    {"name": "Flow Traders",      "token": "flowtraders"},
    {"name": "Bybit",             "token": "bybit"},
    {"name": "OKX",               "token": "okx"},
]

@app.get("/api/greenhouse/companies")
def api_greenhouse_companies():
    return GREENHOUSE_COMPANIES

@app.get("/api/greenhouse/{token}")
def api_greenhouse_jobs(token: str):
    import json as _json
    import urllib.request
    import urllib.error

    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JobSearchHelper/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            jobs = data.get("jobs", [])
            return [
                {
                    "id": j.get("id"),
                    "title": j.get("title"),
                    "location": j.get("location", {}).get("name", ""),
                    "departments": [d.get("name") for d in j.get("departments", [])],
                    "url": j.get("absolute_url"),
                    "updated_at": j.get("updated_at", "")[:10],
                }
                for j in jobs
            ]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(status_code=404, detail=f"No Greenhouse board found for '{token}'")
        raise HTTPException(status_code=502, detail="Greenhouse API error")
    except Exception:
        raise HTTPException(status_code=502, detail="Could not reach Greenhouse")



# --- Workday Job Discovery ---

WORKDAY_COMPANIES = [
    {
        "name": "BlackRock",
        "subdomain": "blackrock.wd1",
        "tenant": "blackrock",
        "board": "BlackRock_Professional",
    },
]

@app.get("/api/workday/companies")
def api_workday_companies():
    return [
        {
            "name": c["name"],
            "key": c["tenant"],
            "board_url": f"https://{c['subdomain']}.myworkdayjobs.com/{c['board']}",
        }
        for c in WORKDAY_COMPANIES
    ]


# --- Chess Hint ---

@app.post("/api/chess/hint")
async def chess_hint(request: Request):
    import json as _json
    import anthropic

    body = await request.json()
    fen = body.get("fen", "")
    if not fen:
        raise HTTPException(status_code=400, detail="FEN required")

    client = anthropic.Anthropic()
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a friendly chess coach helping young children (ages 6-10) learn chess.\n"
                    f"Current board position (FEN): {fen}\n\n"
                    "Suggest the best move for the player whose turn it is.\n"
                    "Respond with ONLY valid JSON (no markdown, no code fences, no extra text):\n"
                    '{\"move\": \"Nf3\", \"from\": \"g1\", \"to\": \"f3\", \"explanation\": \"...\"}\n\n'
                    "Rules:\n"
                    "- \"move\": the move in standard algebraic notation (SAN)\n"
                    "- \"from\" and \"to\": exact square names in lowercase (e.g. \"e2\", \"g1\")\n"
                    "- \"explanation\": 2-3 fun, simple sentences a 7-year-old can understand. "
                    "No chess jargon. Use everyday words. Say which piece moves and why it helps."
                ),
            }],
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])
        return _json.loads(text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hint generation failed: {str(e)}")


# --- Espresso Tracker ---

@app.get("/espresso")
def serve_espresso():
    return FileResponse("static/espresso.html")


class ShotCreate(BaseModel):
    bean_name: str
    dose_grams: float
    bean_origin: str | None = None
    bean_roaster: str | None = None
    roast_level: str | None = None
    yield_grams: float | None = None
    grind_size: int | None = None
    grinder: str | None = None
    tamp_pressure: str | None = None
    brew_time_secs: int | None = None
    water_temp_c: float | None = None
    pressure_bar: float | None = None
    machine: str | None = None
    pre_infusion: int = 0
    taste_notes: str | None = None
    rating: int | None = None
    notes: str | None = None
    shot_date: str | None = None
    shot_time: str | None = None


class ShotUpdate(BaseModel):
    bean_name: str | None = None
    dose_grams: float | None = None
    bean_origin: str | None = None
    bean_roaster: str | None = None
    roast_level: str | None = None
    yield_grams: float | None = None
    grind_size: int | None = None
    grinder: str | None = None
    tamp_pressure: str | None = None
    brew_time_secs: int | None = None
    water_temp_c: float | None = None
    pressure_bar: float | None = None
    machine: str | None = None
    pre_infusion: int | None = None
    taste_notes: str | None = None
    rating: int | None = None
    notes: str | None = None
    shot_date: str | None = None
    shot_time: str | None = None


@app.get("/api/espresso/shots")
def api_espresso_list(days: int | None = None, bean: str | None = None, rating: int | None = None):
    shots = list_shots(days=days, bean=bean, rating=rating)
    return [row_to_dict(s) for s in shots]


@app.get("/api/espresso/shots/{id}")
def api_espresso_get(id: int):
    shot = get_shot(id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return row_to_dict(shot)


@app.post("/api/espresso/shots", status_code=201)
def api_espresso_add(body: ShotCreate):
    new_id = add_shot(**body.model_dump())
    return {"id": new_id}


@app.patch("/api/espresso/shots/{id}")
def api_espresso_update(id: int, body: ShotUpdate):
    if not get_shot(id):
        raise HTTPException(status_code=404, detail="Shot not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if fields:
        update_shot(id, **fields)
    return row_to_dict(get_shot(id))


@app.delete("/api/espresso/shots/{id}", status_code=204)
def api_espresso_delete(id: int):
    if not get_shot(id):
        raise HTTPException(status_code=404, detail="Shot not found")
    delete_shot(id)


@app.get("/api/espresso/stats")
def api_espresso_stats():
    return get_espresso_stats()


@app.get("/api/espresso/beans")
def api_espresso_beans():
    return get_distinct_beans()


@app.get("/api/espresso/equipment")
def api_espresso_equipment():
    return get_distinct_equipment()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
