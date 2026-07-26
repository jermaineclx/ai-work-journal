# AI Work Journal

An AI-powered work intelligence platform that turns casual Telegram
messages into structured, searchable professional work history —
Tasks and their Daily Log timelines — stored in Google Sheets, with an
AI memory layer in SQLite that gets smarter about your projects,
stakeholders and terminology over time.

Full product/architecture/AI/implementation rationale lives in:

- [`01_PRD.md`](01_PRD.md) — product requirements
- [`02_ARCHITECTURE.md`](02_ARCHITECTURE.md) — system architecture
- [`03_IMPLEMENTATION.md`](03_IMPLEMENTATION.md) — implementation guide
- [`04_AI_DESIGN.MD`](04_AI_DESIGN.MD) — AI/prompt/agent design

This build implements the complete Phase 1 MVP described in those
documents: Telegram bot, FastAPI backend, a multi-agent AI pipeline
(extraction → matching → status → tags → resources → impact →
summary), a deterministic Decision Engine, Google Sheets + SQLite
persistence, semantic search, personalised learning (aliases/confidence
history), daily/weekly summaries, reminders, and undo.

## Architecture at a glance

```
Telegram → FastAPI webhook → LogService
                                 │
                                 ▼
                          AI Orchestrator
            (Extraction → Matching → Status → Tags →
                     Resources → Impact)
                                 │
                                 ▼
                        Decision Engine (deterministic)
                     confidence ≥95%  → auto-save
                     confidence 80-94% → ask for confirmation
                     confidence <80%   → clarify / offer candidates
                                 │
                                 ▼
                    Repositories → Google Sheets (Tasks, Daily Logs)
                                 → SQLite (embeddings, aliases, cache)
```

LLM reasoning is **Anthropic Claude**; embeddings for semantic task
matching are **OpenAI** (`text-embedding-3-large`) — Anthropic has no
embeddings API, so this is the one place a second provider is used.
Both sit behind provider-agnostic interfaces (`app/ai/providers/`), so
swapping either is a one-class change.

## Project layout

```
app/
├── api/            FastAPI routes, dependencies, app factory
├── ai/              extraction / matching / classification / summarisation /
│                    embeddings / providers / prompts / evaluation / orchestrator.py
├── core/            config, logging, exceptions, constants, composition root
├── domain/          entities (Task, DailyLog), enums, deterministic business rules
├── integrations/     telegram/, sheets/, (llm/ handled under ai/providers)
├── jobs/            APScheduler jobs (reminders, weekly summary, embedding refresh)
├── memory/          SQLite schema + connection
├── models/          RequestContext (transient, never persisted)
├── repositories/     Task/DailyLog/Memory repositories + Sheets<->entity mappers
├── schemas/          Pydantic I/O contracts (AI output, decisions, API, search)
└── services/         LogService, TaskService, SearchService, SummaryService, ReminderService
tests/                unit tests (domain rules, mappers, LogService w/ fakes)
evaluation/           AI extraction benchmark dataset (manual, needs a real API key)
scripts/              setup/connectivity helper scripts
```

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`. See the comments in `.env.example` for what each value
is and where to get it. In short, you need:

| Variable | Where to get it |
|---|---|
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_ALLOWED_USER_ID` | Your numeric Telegram user ID, e.g. from `@userinfobot` |
| `TELEGRAM_WEBHOOK_SECRET` | Any random string you pick |
| `TELEGRAM_WEBHOOK_URL` | Your public HTTPS URL + `/webhook/telegram` (ngrok locally) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/) (embeddings only) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` or `_FILE` | Google Cloud service account (see below) |
| `GOOGLE_ACCOUNT_EMAIL` | Your personal Google account, so the auto-created sheet is shared with you |
| `GOOGLE_SHEET_ID` | See below — required for personal (non-Workspace) Google accounts |

### 3. Google Cloud setup

1. Create a Google Cloud project, enable the **Google Sheets API** and
   **Google Drive API**.
2. Create a Service Account, generate a JSON key.
3. Put the JSON contents in `GOOGLE_SERVICE_ACCOUNT_JSON` (or save the
   file and point `GOOGLE_SERVICE_ACCOUNT_FILE` at it).
4. Set `GOOGLE_ACCOUNT_EMAIL` to your own Google account.

5. **Create the spreadsheet.** How depends on your account type:

   - **Personal Gmail account (the common case):** service accounts on
     personal Google accounts have **zero Drive storage quota** of
     their own — they can edit files shared with them, but Google
     rejects any attempt to *create* a new file under the service
     account's ownership (`403: storage quota has been exceeded`). So:
     1. Create a blank spreadsheet yourself at
        [sheets.new](https://sheets.new).
     2. Share it with your service account's email (the `client_email`
        field in the JSON key — looks like
        `xxx@yyy.iam.gserviceaccount.com`) with **Editor** access.
     3. Copy the spreadsheet ID from its URL
        (`https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`)
        into `GOOGLE_SHEET_ID`.
   - **Google Workspace account with delegation configured:** you can
     leave `GOOGLE_SHEET_ID` blank and let the app create+share it
     automatically on first run — this only works if the service
     account actually has storage quota available (i.e. domain-wide
     delegation or a Shared Drive), which most individual setups don't.

6. Verify connectivity:

   ```bash
   python scripts/verify_sheets_connection.py
   ```

   With `GOOGLE_SHEET_ID` set, this just opens that sheet and
   provisions the `Tasks`/`Daily Logs` tabs. If left blank and creation
   fails with the storage-quota error above, follow step 5's manual
   path.

### 4. Run locally

```bash
uvicorn main:app --reload
```

Expose it publicly for Telegram (e.g. `ngrok http 8000`), set
`TELEGRAM_WEBHOOK_URL` to the resulting HTTPS URL + `/webhook/telegram`,
and restart — the app registers the webhook with Telegram on startup.

Message your bot on Telegram. Try:

> Finished the settlement SQL today. Finance approved it. QA tomorrow.

### 5. Run with Docker

```bash
docker compose up --build
```

## Testing

```bash
pytest
ruff check .
black --check .
```

Unit tests cover the deterministic layers (Decision Engine, confidence
thresholds, Sheets row mapping, LogService flows) using in-memory fakes
— no network calls, no API keys required.

The AI extraction benchmark (`evaluation/`) is a separate, manual
process that does call the real LLM:

```bash
python scripts/run_evaluation.py
```

## Design notes worth knowing

- **Decision Engine is pure Python, not a prompt.** Confidence
  thresholds (`app/domain/rules/`) are deterministic and configurable
  via `.env`, per the architecture's "AI recommends, the app decides"
  principle.
- **New tasks are never auto-saved**, regardless of confidence —
  creating a persistent workstream is treated as higher-stakes than
  updating an existing one, so it always asks for confirmation.
- **Learning only happens after explicit confirmation** (a button
  tap), never from auto-applied saves — see `LogService.confirm()`.
- **Daily Logs are effectively append-only.** The one exception is
  `/undo`, an explicit user-initiated action to remove the most recent
  log — this is a deliberate, narrow exception, not a general edit API.
- Summary regeneration happens *after* a match is confirmed, not
  speculatively during the AI pipeline — so an unconfirmed/rejected
  match never pollutes a task's stored summary.
