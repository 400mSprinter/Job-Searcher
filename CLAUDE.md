# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conventions
- Add the creation date and time as a comment at the top of every new file (e.g., `// Created: 2026-03-11 10:30`).

## Project: Job Search Helper

A Python CLI tool for tracking job applications, matching postings to a resume via Claude AI, and surfacing follow-up reminders.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Commands

```bash
python main.py add               # Add a new application (interactive)
python main.py list              # List all applications
python main.py list --status Interview  # Filter by status
python main.py update <id>       # Update a field on an application
python main.py delete <id>       # Delete an application
python main.py reminders         # Show applications needing follow-up
python main.py match             # Paste a job posting → get AI fit analysis
python main.py match --file job.txt  # Read posting from file
```

## Architecture

| File | Purpose |
|------|---------|
| `main.py` | Click CLI entry point; imports all modules |
| `db.py` | SQLite init (`jobs.db`) and connection helper |
| `tracker.py` | CRUD for `applications` table; `VALID_STATUSES` list |
| `reminders.py` | Logic for surfacing overdue follow-ups based on status thresholds |
| `matcher.py` | Calls Claude API (Opus 4.6, adaptive thinking, streaming) to analyze job fit |
| `resume.py` | Justin's CV as a plain-text constant (`RESUME_TEXT`) used by the matcher |

## Database

Single SQLite file `jobs.db` (created automatically). Schema:

```
applications(id, company, role, status, date_applied, last_updated, notes, url, contact, follow_up_date)
```

Valid statuses: `Applied`, `Phone Screen`, `Interview`, `Offer`, `Rejected`, `Withdrawn`, `Ghosted`

## Claude API Usage

`matcher.py` uses `claude-opus-4-6` with `thinking: {type: "adaptive"}` and streaming. The `ANTHROPIC_API_KEY` is loaded from `.env` via `python-dotenv`.

## Project: Espresso Tracker

A mobile-friendly web app for tracking espresso shots — beans, dose/yield/ratio, grind, tamp, brew time, taste notes, and ratings.

### Architecture

| File | Purpose |
|------|---------|
| `espresso/espresso_db.py` | SQLite init (`espresso.db`) and connection helper |
| `espresso/espresso_tracker.py` | CRUD for `shots` table |
| `espresso/espresso_stats.py` | Aggregated stats: averages, weekly trends, top beans, best shot |
| `static/espresso.html` | Self-contained SPA frontend (dark theme, mobile-optimized) |

### Database

Single SQLite file `espresso.db` (created automatically). Schema:

```
shots(id, bean_name, bean_origin, bean_roaster, roast_level,
      dose_grams, yield_grams, brew_ratio, grind_size, grinder,
      tamp_pressure, brew_time_secs, water_temp_c, pressure_bar,
      machine, pre_infusion, taste_notes, rating, notes,
      shot_date, shot_time, created_at)
```

### API Endpoints

All under `/api/espresso/`:
- `GET /shots` — list shots (optional `?days=`, `?bean=`, `?rating=` filters)
- `POST /shots` — create shot
- `PATCH /shots/{id}` — update shot
- `DELETE /shots/{id}` — delete shot
- `GET /stats` — aggregated statistics
- `GET /beans` — distinct bean names (autocomplete)
- `GET /equipment` — distinct grinders/machines (autocomplete)

Page served at `/espresso`.
