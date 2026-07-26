# WorkGraph AI

# Implementation Guide

**Document Version:** 1.0 (Draft)
**Status:** Implementation Guide – Phase 1 (MVP)

**Related Documents**

* `01_PRD.md`
* `02_ARCHITECTURE.md`
* `03_AI_DESIGN.md`

---

# 1. Introduction

## Purpose

This document describes **how WorkGraph AI will be implemented** from an engineering perspective.

Unlike the PRD, which defines product behaviour, and the Architecture document, which defines system design, this guide focuses on translating those decisions into production-ready code.

The objective is that a developer can clone the repository, follow this guide, and build the MVP without ambiguity.

---

## Scope

This implementation guide covers:

* local development
* environment setup
* project scaffolding
* coding conventions
* implementation order
* service implementation
* deployment
* testing

This document assumes the reader has basic familiarity with Python, Git and REST APIs.

---

# 2. Development Principles

The implementation should follow several guiding principles.

---

## Build Vertically

Implement complete user journeys rather than isolated components.

Preferred order:

```text id="mjlwm5"
Telegram

↓

API

↓

AI

↓

Google Sheets

↓

User Confirmation
```

Instead of:

* writing all repositories
* then all services
* then all APIs

Building vertically allows features to become usable much earlier.

---

## Keep Components Small

Prefer multiple focused classes over large "god classes".

Example:

```text id="jv6ymz"
TaskMatcher

SummaryGenerator

ReminderScheduler

LogRepository
```

Rather than:

```text id="yj8lbx"
WorkGraphManager
```

---

## Avoid Premature Optimisation

The MVP supports one user.

Optimise for:

* readability
* correctness
* maintainability

Not:

* distributed systems
* microservices
* extreme scalability

---

## Business Logic Lives in Code

Prompts should extract information.

They should **not** enforce business rules.

Example:

LLM:

> Stakeholder = Finance

Application:

```text id="l2vjnv"
if confidence < 0.90

↓

Ask user
```

---

## Make Every Feature Testable

Every service should be testable independently.

Good:

```text id="l9jny0"
TaskMatcher

↓

Unit Test
```

Bad:

Telegram Bot

↓

TaskMatcher

↓

Impossible to test independently

---

# 3. Recommended Development Environment

## Operating System

Recommended:

* macOS
* Linux

Windows is supported but not the primary development target.

---

## Python Version

Recommended:

```text id="9n4qjm"
Python 3.12+
```

Avoid older Python versions unless required by dependencies.

---

## IDE

Recommended:

* Visual Studio Code

Recommended extensions:

* Python
* Ruff
* Pylance
* Docker
* GitLens
* Markdown All in One

---

## Version Control

Use Git from the beginning.

Recommended branching strategy:

```text id="xzjx1t"
main

↓

develop

↓

feature/*
```

Example:

```text id="gnz4wi"
feature/task-matching

feature/google-sheets

feature/telegram
```

---

# 4. Technology Stack

## Backend

| Technology          | Purpose              |
| ------------------- | -------------------- |
| Python              | Primary language     |
| FastAPI             | Backend API          |
| Uvicorn             | ASGI server          |
| Pydantic            | Validation           |
| SQLAlchemy (future) | Database abstraction |
| SQLite              | AI metadata          |

---

## AI

| Technology            | Purpose                   |
| --------------------- | ------------------------- |
| OpenAI API            | Language understanding    |
| OpenAI Embeddings     | Semantic search           |
| Instructor (optional) | Structured JSON responses |
| tiktoken              | Token estimation          |

The AI layer should be provider-agnostic so alternative models can be introduced later.

---

## Storage

| Technology        | Purpose          |
| ----------------- | ---------------- |
| Google Sheets API | Business records |
| SQLite            | AI memory        |

---

## Telegram

| Technology          | Purpose              |
| ------------------- | -------------------- |
| python-telegram-bot | Telegram integration |

---

## Development

| Technology             | Purpose               |
| ---------------------- | --------------------- |
| Poetry *(recommended)* | Dependency management |
| Pytest                 | Testing               |
| Ruff                   | Linting               |
| Black                  | Formatting            |
| pre-commit             | Git hooks             |

---

## Deployment

| Technology     | Purpose          |
| -------------- | ---------------- |
| Docker         | Containerisation |
| Railway        | Hosting          |
| GitHub Actions | CI/CD            |

---

# 5. Local Development Setup

## Step 1 — Create Repository

```bash
git init workgraph-ai
cd workgraph-ai
```

---

## Step 2 — Create Virtual Environment

Using Poetry:

```bash
poetry init
poetry shell
```

Or using `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Step 3 — Install Dependencies

Core dependencies:

```bash
pip install fastapi
pip install uvicorn
pip install openai
pip install python-telegram-bot
pip install gspread
pip install google-auth
pip install pydantic
pip install python-dotenv
pip install rapidfuzz
pip install sentence-transformers
```

Development dependencies:

```bash
pip install pytest
pip install ruff
pip install black
pip install pre-commit
```

Later phases may introduce additional packages as required.

---

## Step 4 — Project Structure

Initial scaffold:

```text id="w9xihj"
workgraph-ai/

app/
tests/
docs/
scripts/

.env
.gitignore
README.md
requirements.txt
main.py
```

The remaining directories will be introduced incrementally.

---

## Step 5 — Configure Git

Recommended `.gitignore`:

```text id="bl4gbd"
.venv/

__pycache__/

.env

*.sqlite

.pytest_cache/

.vscode/
```

API credentials should never be committed.

---

# 6. Environment Configuration

All configuration should be stored in environment variables.

Example:

```text id="rv9dkx"
TELEGRAM_TOKEN=

OPENAI_API_KEY=

GOOGLE_SERVICE_ACCOUNT=

GOOGLE_SHEET_ID=

DATABASE_PATH=data/workgraph.db

LOG_LEVEL=INFO
```

Never hardcode credentials.

---

## Configuration Management

Use `pydantic-settings` (or `BaseSettings`) to centralise configuration.

Example:

```text id="7gw7ga"
settings.py

↓

load .env

↓

Application
```

Benefits:

* type safety
* validation
* central configuration
* easier deployment

---

# 7. Google Cloud Setup

## Overview

Google Sheets serves as the primary business datastore.

To access it programmatically, the application requires a Google Cloud Service Account.

---

## Step 1 — Create Google Cloud Project

Recommended project name:

```text id="e2y5mu"
workgraph-ai
```

---

## Step 2 — Enable APIs

Enable:

* Google Sheets API
* Google Drive API

These are required for spreadsheet access.

---

## Step 3 — Create Service Account

Recommended name:

```text id="7dhh7g"
workgraph-service
```

Generate a JSON credentials file.

Store it securely.

Never commit it to Git.

---

## Step 4 — Share Spreadsheet

Share the Google Sheet with the Service Account email.

Example:

```text id="krhmsz"
workgraph-service@project.iam.gserviceaccount.com
```

Grant:

Editor permissions

This allows the application to:

* read Tasks
* append Daily Logs
* update summaries

---

## Step 5 — Verify Connectivity

Before writing application code, verify that:

* authentication succeeds
* spreadsheet opens
* worksheets can be read
* worksheets can be updated

A simple connectivity script should be created during initial setup.

---

# 8. Telegram Bot Setup

## Overview

Telegram is the primary user interface for the MVP.

The bot should remain intentionally lightweight.

All intelligence resides within the backend.

---

## Step 1 — Create Bot

Using **BotFather**:

Create:

```text id="pvsl75"
@WorkGraphBot
```

Obtain:

```text id="tcb6h5"
BOT_TOKEN
```

Store this token in `.env`.

---

## Step 2 — Configure Webhook

During local development, use a tunnelling service such as:

* ngrok
* Cloudflare Tunnel

Example flow:

```text id="o2pr2m"
Telegram

↓

Webhook

↓

https://xxxxx.ngrok.app

↓

FastAPI
```

This enables Telegram to communicate with your local development server.

---

## Step 3 — Verify Webhook

Test by sending:

> hello

Expected result:

```text id="jlwm2e"
Webhook Received

↓

FastAPI Endpoint

↓

Telegram Reply

↓

Success
```

No AI integration is required at this stage.

The goal is simply to confirm end-to-end communication.

---

# 9. Development Milestones (Phase 1)

To reduce complexity, implementation should follow incremental milestones.

| Milestone | Goal                                   |
| --------- | -------------------------------------- |
| M1        | Telegram bot responds to messages      |
| M2        | Google Sheets connectivity established |
| M3        | FastAPI backend running locally        |
| M4        | Environment configuration complete     |
| M5        | Project structure scaffolded           |
| M6        | Basic logging configured               |
| M7        | Development workflow verified          |

Each milestone should be completed and tested before progressing to the next.

---

# 10. Coding Standards

## Naming

Classes:

```text id="5z9gwm"
TaskRepository

DailyLogService

SummaryGenerator
```

Functions:

```text id="0lhgku"
match_task()

generate_summary()

save_log()
```

Variables:

```text id="g9bnlc"
task_id

stakeholder_name

confidence_score
```

Use descriptive names over abbreviations.

---

## Type Hints

All public functions should include type hints.

This improves readability, editor support and maintainability.

---

## Docstrings

Public classes and methods should include concise docstrings describing:

* purpose
* parameters
* return values

---

## Formatting

Use:

* Black for formatting
* Ruff for linting

Automate both using pre-commit hooks.

---

## Logging

Prefer structured logging over `print()` statements.

Include:

* request ID
* execution time
* confidence score
* service name

Avoid logging sensitive business content unless required for debugging.

---

# Part 1 Summary

This section establishes the engineering foundation required before implementing business features.

By the end of Part 1, the development environment should support:

* A reproducible Python environment with all core dependencies installed.
* A structured project scaffold following Clean Architecture principles.
* Secure configuration management using environment variables.
* A configured Google Cloud project with access to Google Sheets.
* A Telegram bot capable of communicating with a local FastAPI server.
* Consistent coding standards, tooling and development workflows.

With these foundations in place, the next phase will focus on implementing the backend itself, beginning with project scaffolding, repository abstractions, API endpoints and integrations with Google Sheets and SQLite.

# 11. Project Scaffolding

## Overview

With the development environment ready, the next step is to scaffold the application following the architecture defined in `02_ARCHITECTURE.md`.

The objective at this stage is **not** to build features, but to establish a clean foundation that supports future growth.

---

## Final Directory Structure

```text
workgraph-ai/

├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── dependencies.py
│   │   └── router.py
│   │
│   ├── ai/
│   │   ├── extraction/
│   │   ├── matching/
│   │   ├── summarisation/
│   │   ├── embeddings/
│   │   ├── providers/
│   │   └── prompts/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── constants.py
│   │   └── exceptions.py
│   │
│   ├── domain/
│   │   ├── entities/
│   │   ├── enums/
│   │   └── rules/
│   │
│   ├── integrations/
│   │   ├── telegram/
│   │   ├── sheets/
│   │   └── llm/
│   │
│   ├── memory/
│   │
│   ├── models/
│   │
│   ├── repositories/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │
│   └── utils/
│
├── tests/
│
├── docs/
│
├── scripts/
│
├── data/
│
├── main.py
└── requirements.txt
```

Every folder should have a clearly defined responsibility.

---

# 12. Core Domain Models

## Philosophy

WorkGraph AI revolves around a small number of domain entities.

These entities should be represented as Python models independent of Google Sheets.

Google Sheets becomes merely a persistence layer.

---

# Task

Represents a long-running work item.

Suggested fields:

```text
Task

task_id

title

stakeholder

status

summary

tags

resources

created_at

updated_at
```

The Task object should contain validation but no storage logic.

---

# DailyLog

Represents a single Telegram submission.

```text
DailyLog

log_id

task_id

date

message

stakeholder

status

next_steps

resources

tags

timestamp
```

Daily Logs are immutable after creation.

Corrections generate updates rather than replacing historical context.

---

# SearchResult

Used internally when matching tasks.

```text
SearchResult

task_id

similarity_score

confidence

reason
```

This object should never be persisted.

---

# AIExtraction

Represents structured output from the LLM.

```text
AIExtraction

stakeholder

task

status

resources

tags

next_steps

confidence
```

Keeping AI output isolated makes debugging significantly easier.

---

# 13. Repository Layer

## Overview

Repositories isolate application logic from storage.

Application Services never interact directly with Google Sheets.

---

## Why Repositories?

Without repositories:

```text
Service

↓

Google Sheets API
```

Every service becomes tightly coupled to Google APIs.

Instead:

```text
Application Service

↓

Repository

↓

Google Sheets
```

Storage can later change without modifying business logic.

---

## Repository Interfaces

Recommended repositories:

```text
TaskRepository

DailyLogRepository

SummaryRepository

MemoryRepository
```

Each repository owns one persistence concern.

---

# TaskRepository

Responsibilities:

* retrieve tasks
* retrieve task by ID
* create task
* update task
* search active tasks

Should never perform AI operations.

---

# DailyLogRepository

Responsibilities:

* append log
* retrieve logs
* retrieve logs by task
* retrieve logs by date

Daily Logs should only be appended.

---

# SummaryRepository

Responsibilities:

* read summaries
* update summaries

Summary generation belongs to the AI Layer.

Persistence belongs here.

---

# MemoryRepository

Stores AI-specific information.

Examples:

* embeddings
* aliases
* confidence history
* learned abbreviations

SQLite is recommended for the MVP.

---

# Repository Pattern Example

```text
TaskService

↓

TaskRepository

↓

GoogleSheetsClient

↓

Google Sheets API
```

Repositories shield the rest of the application from API implementation details.

---

# 14. Google Sheets Integration

## Overview

Google Sheets serves as the primary business datastore.

Rather than exposing raw worksheet operations, create a dedicated client.

---

# GoogleSheetsClient

Responsibilities:

* authenticate
* open spreadsheet
* retrieve worksheets
* append rows
* update rows
* batch updates

Other services should never call gspread directly.

---

# Worksheets

The client should expose methods similar to:

```text
get_tasks_sheet()

get_daily_logs_sheet()

append_task()

append_log()

update_task()

find_task()
```

This creates a stable abstraction over spreadsheet operations.

---

# Batch Updates

Where possible, related changes should be grouped into a single batch request.

Benefits:

* lower latency
* fewer API calls
* reduced quota usage

---

# Retry Strategy

Google API calls should automatically retry:

* transient network failures
* HTTP 429
* temporary server errors

Use exponential backoff.

---

# Row Mapping

Avoid exposing spreadsheet row numbers to application logic.

Repositories should translate:

```text
Task

↓

Spreadsheet Row

↓

Task Object
```

The rest of the application should never know row indices.

---

# 15. SQLite Memory Layer

## Purpose

SQLite stores AI-specific metadata that should not appear inside Google Sheets.

Examples:

```text
Alias

↓

Finance Team

↓

Finance
```

or

```text
Prod

↓

Product
```

---

# Suggested Tables

```text
aliases

embeddings

preferences

statistics

cache
```

These tables support AI behaviour rather than business records.

---

# Embeddings Table

Suggested fields:

```text
embedding_id

task_id

vector

updated_at
```

Vectors enable semantic task matching.

---

# Preferences Table

Stores learned behaviour.

Examples:

* preferred terminology
* common abbreviations
* default stakeholders

These preferences should only be updated after explicit user confirmation.

---

# Cache Table

Used to reduce unnecessary LLM calls.

Potential cache items:

* summaries
* embeddings
* extraction outputs

Caching should include expiration timestamps.

---

# 16. Service Layer

## Philosophy

Services coordinate business workflows.

Repositories manage persistence.

AI modules perform reasoning.

Services connect these components together.

---

# LogService

Responsible for processing new Daily Logs.

Workflow:

```text
Receive Message

↓

AI Extraction

↓

Task Matching

↓

Decision Engine

↓

Repositories

↓

Response
```

This is the primary entry point for new work logs.

---

# TaskService

Responsibilities:

* create task
* update task
* retrieve tasks
* archive tasks
* merge tasks (future)

TaskService should not contain AI extraction logic.

---

# SearchService

Responsibilities:

* keyword search
* semantic search
* task lookup
* stakeholder lookup

Initially this can rely on embeddings stored in SQLite.

---

# SummaryService

Responsibilities:

* update rolling summaries
* weekly summaries
* monthly summaries

Summary generation uses the AI Layer.

Storage uses repositories.

---

# ReminderService

Handles recurring reminders.

Examples:

* daily reminder
* end-of-week reminder

Future reminders may be personalised.

---

# 17. FastAPI Implementation

## Application Entry Point

Recommended structure:

```text
main.py

↓

FastAPI()

↓

Include Routers

↓

Start Server
```

The entry point should remain minimal.

---

# API Routers

Suggested routes:

```text
/api

/webhook

/health

/version
```

Future additions:

```text
/search

/tasks

/logs

/admin
```

---

# Telegram Webhook

Telegram sends all messages here.

Responsibilities:

* validate request
* extract payload
* forward to LogService

The webhook should avoid business logic.

---

# Health Endpoint

Purpose:

Confirm application status.

Checks:

* FastAPI
* Google Sheets
* SQLite
* LLM Provider

Return:

```json
{
  "status": "healthy"
}
```

---

# Error Handling

Errors should be converted into structured responses.

Avoid exposing internal stack traces.

Example:

```json
{
    "error":"Unable to process request",
    "request_id":"abc123"
}
```

Detailed logs remain internal.

---

# 18. Telegram Integration

## Overview

Telegram should behave as a conversational interface rather than a command-line tool.

Natural language is preferred over rigid commands.

---

# Incoming Messages

Typical messages:

> Investigated settlement issue today.

> Finance approved dashboard.

> Waiting for Product feedback.

All messages should pass through the same processing pipeline.

---

# Suggested Commands

```text
/help

/search

/tasks

/today

/summary

/settings
```

Commands complement natural conversation but should not be required.

---

# Inline Buttons

Medium-confidence decisions should use Telegram inline keyboards.

Example:

```text
Matched task:

Settlement Reconciliation

Confidence: 84%

[Confirm]

[Choose Another]

[Create New]
```

This reduces typing while keeping users in control.

---

# Rich Responses

Whenever possible, responses should be concise and structured.

Example:

```text
✓ Daily Log Saved

Task:
Settlement Reconciliation

Stakeholder:
Finance

Status:
Waiting QA

Summary Updated
```

The objective is to reassure the user that their work has been captured correctly without overwhelming them with information.

---

# Part 2 Summary

At the end of this phase, the core backend infrastructure should be operational.

Key implementation outcomes include:

* A clean project scaffold following Clean Architecture principles.
* Domain models representing Tasks, Daily Logs and AI outputs independently of storage.
* Repository abstractions separating business logic from Google Sheets and SQLite.
* A dedicated Google Sheets client handling authentication, batching and retries.
* An SQLite memory layer supporting embeddings, caching and personalised AI behaviour.
* Application services orchestrating workflows while delegating reasoning and persistence to specialised components.
* A FastAPI application exposing Telegram webhooks, health checks and foundational endpoints.
* A conversational Telegram interface with support for natural language and inline confirmations.

With these components in place, the application is ready for the next stage: implementing the AI layer, prompt orchestration, decision engine, semantic search and background jobs that transform WorkGraph AI from a CRUD application into an intelligent work logging assistant.


# 19. AI Layer Implementation

## Overview

The AI Layer is responsible for transforming unstructured conversations into structured work records.

Unlike traditional CRUD applications, the AI layer is probabilistic. Therefore, every output should be treated as a recommendation rather than absolute truth.

The implementation should prioritise:

* deterministic workflows
* structured outputs
* explainability
* modularity
* provider independence

---

# AI Module Structure

```text id="wvf9gh"
app/

└── ai/

    ├── providers/
    ├── extraction/
    ├── matching/
    ├── summarisation/
    ├── embeddings/
    ├── prompts/
    ├── evaluation/
    └── orchestrator.py
```

Each module owns a single AI capability.

---

# AI Orchestrator

The AI Orchestrator coordinates specialised AI modules.

Responsibilities:

* invoke extraction
* invoke task matching
* invoke status classification
* invoke summary generation
* collect outputs
* return a unified response

Example flow:

```text id="uytxsv"
User Message

↓

AI Orchestrator

↓

Extraction

↓

Task Matching

↓

Status Detection

↓

Tag Generation

↓

Summary

↓

Structured Response
```

The orchestrator should contain no prompt logic itself.

---

# LLM Provider Interface

The application should depend on an abstraction rather than a specific SDK.

Example:

```text id="qix61g"
LLMProvider

↓

OpenAIProvider

GeminiProvider

ClaudeProvider
```

This enables provider switching with minimal code changes.

---

# Structured Outputs

Every AI call should return validated JSON rather than free-form text.

Example:

```json id="rw9ljf"
{
  "stakeholder": "Finance",
  "task": "Settlement Reconciliation",
  "status": "Waiting QA",
  "next_steps": "QA testing tomorrow",
  "confidence": 0.93
}
```

Using structured outputs simplifies validation and downstream processing.

---

# Prompt Organisation

Store prompts as version-controlled Markdown files.

Example:

```text id="z8r1qo"
prompts/

extract_entities.md

match_task.md

generate_summary.md

weekly_summary.md

career_summary.md
```

Each prompt should:

* define its objective
* specify output schema
* include few-shot examples where appropriate
* include version metadata

Avoid embedding prompts directly inside Python files.

---

# Prompt Versioning

Every AI response should record the prompt version used.

Example:

```text id="jdlr9h"
Prompt

extract_entities_v3

↓

Response

↓

Saved in Logs
```

This enables evaluation after prompt updates.

---

# 20. Decision Engine

## Philosophy

The Decision Engine converts probabilistic AI outputs into deterministic application behaviour.

It is the bridge between AI and business logic.

---

# Responsibilities

The Decision Engine determines:

* whether confidence is sufficient
* whether confirmation is required
* whether a task should be created
* whether summaries should be updated
* whether repositories should be called

---

# Decision Pipeline

```text id="1k7n4w"
AI Response

↓

Validation

↓

Confidence Evaluation

↓

Business Rules

↓

Decision

↓

Persistence
```

---

# Confidence Thresholds

Suggested thresholds:

| Confidence | Behaviour                                             |
| ---------- | ----------------------------------------------------- |
| ≥95%       | Automatically apply changes and notify the user.      |
| 80–94%     | Present recommendation for confirmation.              |
| <80%       | Ask clarifying questions or present multiple options. |

Thresholds should be configurable rather than hardcoded.

---

# Rule Examples

Example:

```text id="tq29me"
Matched Existing Task

Confidence = 98%

↓

Automatically attach log
```

Example:

```text id="gxf25v"
Matched Existing Task

Confidence = 76%

↓

Ask user
```

The same AI output should always produce the same decision under identical rules.

---

# User Corrections

Corrections should feed into the learning system.

Example:

```text id="lkh8on"
AI

↓

Task A

↓

User selects Task B

↓

Save correction

↓

Improve future matching
```

The Decision Engine itself remains deterministic.

---

# 21. Semantic Search

## Overview

Task matching should rely on semantic similarity rather than exact keyword matching.

This allows the system to understand different ways of referring to the same work.

Example:

```text id="u8pdkr"
Settlement SQL

≈

Finance reconciliation query
```

---

# Search Pipeline

```text id="ol7sk1"
User Message

↓

Embedding Generation

↓

Similarity Search

↓

Top Candidates

↓

LLM Verification

↓

Best Match
```

Embeddings provide fast retrieval while the LLM performs contextual reasoning.

---

# Embedding Generation

Each Task should maintain an embedding generated from:

* title
* summary
* stakeholder
* recent updates
* tags

These embeddings are stored in SQLite during the MVP.

---

# Similarity Search

Suggested process:

1. Generate embedding for incoming message.
2. Compute similarity against stored task embeddings.
3. Retrieve the top 5 candidates.
4. Pass candidates to the LLM for final ranking.

This hybrid approach balances speed and accuracy.

---

# Fallback Strategy

If semantic similarity is weak:

* present likely candidates
* offer "Create New Task"
* request clarification

The application should avoid creating duplicate tasks whenever possible.

---

# 22. Background Jobs

## Philosophy

Not every operation needs to happen synchronously.

Background jobs improve responsiveness by handling non-critical work after the user receives confirmation.

---

# Recommended Jobs

Examples:

```text id="2kl3vw"
Daily Reminder

Weekly Summary

Monthly Summary

Embedding Refresh

Summary Regeneration

Cache Cleanup
```

---

# Job Scheduler

Recommended options:

* APScheduler
* Celery (future)
* Railway Cron

For the MVP, APScheduler provides sufficient functionality.

---

# Embedding Refresh Job

Whenever a Task changes significantly:

```text id="1h1x9s"
Task Updated

↓

Queue Refresh

↓

Regenerate Embedding

↓

Save SQLite
```

This keeps search results current without delaying user interactions.

---

# Summary Regeneration

Task summaries should be regenerated asynchronously when:

* multiple new logs are added
* a task status changes
* significant milestones occur

The user should not wait for summarisation before receiving confirmation.

---

# Reminder Scheduler

Daily reminders encourage consistent logging.

Example schedule:

* Weekdays at 6:00 PM

Message:

> 👋 What did you work on today?

Future versions may personalise reminder timing.

---

# Weekly Summary Job

Every Friday evening:

```text id="9hjlwm"
Collect Logs

↓

Generate Weekly Summary

↓

Send Telegram Message
```

Example output:

> This week you completed three tasks, started one new initiative and worked primarily with Finance and Product.

---

# Monthly Summary

The monthly summary aggregates:

* completed tasks
* active stakeholders
* major achievements
* work trends

This forms the foundation for future performance reviews and career intelligence.

---

# 23. AI Learning System

## Philosophy

The AI should improve only through confirmed user behaviour.

The system should never learn from uncertain or rejected predictions.

---

# Learning Pipeline

```text id="dwzkdg"
Prediction

↓

User Confirmation

↓

Store Feedback

↓

Update Knowledge Base

↓

Improve Future Predictions
```

---

# Learned Information

Examples:

* preferred terminology
* abbreviations
* stakeholder aliases
* recurring project names
* task naming conventions

These are stored in SQLite.

---

# Knowledge Base Updates

Example:

```text id="drhyg5"
Prod

↓

Product
```

After repeated confirmation, the alias becomes part of the user's knowledge base.

---

# Adaptive Confidence

Confidence should increase when the AI repeatedly succeeds with similar inputs.

Example:

Month 1

```text id="hbmh1x"
AUM Dashboard

Confidence

71%
```

Month 6

```text id="g0jlwm"
AUM Dashboard

Confidence

98%
```

This reflects learned familiarity rather than changes to the language model.

---

# 24. Weekly & Monthly Reports

## Weekly Report

Inputs:

* Daily Logs
* Task updates
* completed work
* stakeholder activity

Outputs:

* concise summary
* accomplishments
* pending work
* next week's priorities

The report should be suitable for forwarding to a manager with minimal editing.

---

# Monthly Report

Monthly reports should identify:

* recurring projects
* business impact
* workload trends
* stakeholder distribution
* major achievements

Future versions may automatically draft performance review content.

---

# 25. Notification System

## Notification Types

The MVP supports:

* confirmation messages
* reminder notifications
* weekly summaries
* monthly summaries

Future notifications:

* milestone celebrations
* inactivity reminders
* overdue task prompts

---

# Delivery Principles

Notifications should be:

* timely
* concise
* actionable

Avoid overwhelming users with unnecessary messages.

---

# 26. AI Evaluation

## Why Evaluation Matters

Prompt changes should be measured rather than assumed to be improvements.

Evaluation enables consistent quality over time.

---

# Suggested Evaluation Dataset

Create a folder:

```text id="cxzjzi"
evaluation/

sample_logs/

expected_outputs/
```

Include approximately 100 representative Daily Logs covering different stakeholders, statuses and writing styles.

---

# Evaluation Metrics

Track:

* task matching accuracy
* stakeholder extraction accuracy
* status classification accuracy
* summary quality
* user confirmation rate

Future versions may include automated regression testing for prompts.

---

# Manual Review

Before deploying prompt updates:

1. Run evaluation dataset.
2. Compare against previous version.
3. Review failures.
4. Deploy only if overall quality improves.

This prevents regressions caused by prompt modifications.

---

# Part 3 Summary

This section implements the intelligence of WorkGraph AI.

The AI layer is organised into specialised modules coordinated by an orchestrator, while the Decision Engine converts probabilistic outputs into deterministic application behaviour. Semantic search combines embeddings with LLM reasoning to improve task matching, and background jobs handle asynchronous operations such as reminders, embedding refreshes and summary generation.

A personalised learning system enables the application to become more accurate over time based only on confirmed user interactions, while evaluation datasets and prompt versioning provide a disciplined approach to measuring AI quality.

With these components complete, WorkGraph AI evolves from a messaging application into an intelligent assistant capable of understanding work context, maintaining project continuity and producing meaningful professional insights over time.


# 27. Testing Strategy

## Philosophy

WorkGraph AI combines deterministic application logic with probabilistic AI behaviour. The testing strategy therefore treats these two categories differently.

* Deterministic logic should have predictable unit and integration tests.
* AI behaviour should be evaluated against representative datasets and quality metrics rather than exact text matching.

The objective is to ensure every release is reliable without preventing iteration on prompts and models.

---

# Testing Pyramid

```text id="9a2hdk"
                End-to-End Tests
                      ▲
             Integration Tests
                      ▲
                Unit Tests
```

Unit tests should make up the majority of the test suite.

---

# Unit Tests

Each module should be testable in isolation.

Examples:

* Task matching rules
* Repository methods
* Decision Engine
* Validation logic
* Utility functions

External APIs should be mocked.

Example:

```text id="hd20zg"
DecisionEngine

↓

Input

↓

Expected Decision
```

---

# Integration Tests

Integration tests verify that multiple components work together.

Examples:

* Telegram → FastAPI
* FastAPI → AI Orchestrator
* Repository → Google Sheets
* Repository → SQLite

These tests may use dedicated test spreadsheets and temporary SQLite databases.

---

# End-to-End Tests

End-to-end tests simulate real user behaviour.

Example scenario:

```text id="7uzj7o"
Telegram Message

↓

Webhook

↓

AI Extraction

↓

Task Matching

↓

Google Sheets Updated

↓

Telegram Confirmation
```

The expected result is verified against both user-visible responses and stored records.

---

# AI Evaluation Tests

Unlike traditional unit tests, AI evaluation measures quality.

Maintain a benchmark dataset containing:

* informal messages
* short updates
* long updates
* ambiguous cases
* corrections

Each benchmark should include expected structured outputs.

Metrics include:

* extraction accuracy
* task matching accuracy
* confirmation rate
* false positive rate

---

# Regression Testing

Before each release:

* run unit tests
* run integration tests
* run AI evaluation suite
* compare results with previous release

Deployment should only proceed if quality remains stable or improves.

---

# Test Coverage Goals

| Component    |        Target Coverage |
| ------------ | ---------------------: |
| Domain Rules |                   95%+ |
| Services     |                   90%+ |
| Repositories |                   90%+ |
| Utilities    |                   95%+ |
| AI Modules   | Behavioural evaluation |

---

# 28. Logging Strategy

## Philosophy

Logs should explain what happened without exposing sensitive work content.

Logging is primarily intended for:

* debugging
* monitoring
* performance analysis
* prompt evaluation

---

# Structured Logging

Each log entry should include:

```text id="uxp0p9"
Timestamp

Request ID

User ID

Service

Latency

Confidence

Result
```

Structured formats (e.g. JSON) are recommended for future observability platforms.

---

# Log Levels

Suggested usage:

| Level    | Purpose              |
| -------- | -------------------- |
| DEBUG    | Local development    |
| INFO     | Normal operations    |
| WARNING  | Recoverable issues   |
| ERROR    | Failures             |
| CRITICAL | System-wide failures |

Production environments should generally run at `INFO`.

---

# Sensitive Data

Avoid logging:

* API keys
* credentials
* Google tokens
* full confidential work descriptions

When possible, log metadata rather than raw message content.

---

# Request Tracing

Every request should receive a unique identifier.

Example:

```text id="rqf1ph"
REQ-20260726-001
```

This identifier should appear in:

* API logs
* AI logs
* repository logs
* error logs

This simplifies debugging across multiple services.

---

# 29. Deployment

## Deployment Philosophy

The MVP should be deployable by a single developer in minutes.

Recommended platform:

* Railway

Alternative options:

* Render
* Fly.io
* Google Cloud Run

---

# Docker

The application should run entirely inside a Docker container.

Recommended stages:

```text id="9tkm2z"
Build

↓

Install Dependencies

↓

Copy Source

↓

Start FastAPI
```

Using Docker ensures development and production remain consistent.

---

# Railway Deployment

Deployment flow:

```text id="6y3q2d"
GitHub Push

↓

GitHub Actions

↓

Railway Deploy

↓

Application Online
```

Required environment variables should be configured within Railway rather than committed to the repository.

---

# Persistent Storage

During the MVP:

Business Data

* Google Sheets

AI Memory

* SQLite (mounted persistent volume if available)

If persistent disks are unavailable, plan a future migration to PostgreSQL.

---

# Secrets

Production secrets include:

* Telegram token
* OpenAI API key
* Google Service Account credentials

Store them using the hosting provider's secret management system.

---

# 30. CI/CD

## Objective

Every change should automatically:

* build
* test
* lint
* deploy (if appropriate)

This minimises manual deployment effort.

---

# GitHub Actions Pipeline

Recommended workflow:

```text id="bdapdy"
Push

↓

Install Dependencies

↓

Run Ruff

↓

Run Black Check

↓

Run Pytest

↓

Build Docker

↓

Deploy
```

Deployment should only occur if all checks pass.

---

# Branch Strategy

Suggested workflow:

```text id="mm0vh7"
main

↓

develop

↓

feature/*
```

Only merge into `main` after:

* code review (if applicable)
* successful tests
* passing AI evaluation

---

# Release Tags

Suggested versioning:

```text id="p3epql"
v0.1.0

v0.2.0

v1.0.0
```

Maintain a changelog documenting:

* new features
* bug fixes
* prompt updates
* architectural changes

---

# 31. Monitoring & Operations

## Health Monitoring

Expose endpoints:

```text id="d3nqys"
/health

/ready

/version
```

The health endpoint should verify:

* Google Sheets access
* SQLite availability
* LLM provider reachability

---

# Metrics

Suggested metrics:

Performance

* average latency
* AI response time
* Google API latency

Usage

* logs submitted
* tasks created
* reminders sent

AI Quality

* confirmation rate
* correction rate
* confidence distribution

Cost

* LLM token usage
* estimated API spend
* embedding generation count

---

# Alerting

Future versions may notify the owner if:

* webhook fails
* Google Sheets becomes unavailable
* AI provider fails
* scheduled jobs stop executing

The MVP can initially rely on platform logs.

---

# 32. Performance Optimisation

## Current Priorities

The MVP prioritises correctness over raw speed.

However, several optimisations are recommended.

---

# Caching

Cache frequently accessed information:

* active tasks
* embeddings
* summaries
* aliases

Avoid repeatedly querying Google Sheets for unchanged data.

---

# Batch Operations

When updating multiple spreadsheet cells:

Use batch updates instead of individual requests.

Benefits:

* reduced latency
* fewer API calls
* lower quota usage

---

# Async Processing

Use asynchronous tasks for:

* summary generation
* embedding refresh
* reminder scheduling

The user should receive confirmation before these background tasks complete.

---

# Lazy Loading

Only load data when required.

Example:

Do not load the full Daily Log history if only active Tasks are needed.

---

# 33. Security Checklist

Before deployment, verify:

* All secrets stored securely.
* `.env` excluded from Git.
* Service Account credentials protected.
* HTTPS enabled.
* Input validation implemented.
* Request IDs generated.
* Logging sanitised.
* Dependency versions reviewed.
* Backups tested.
* Error messages do not expose internals.

This checklist should be completed before each production release.

---

# 34. MVP Completion Checklist

The MVP is considered complete when all of the following are operational.

## Core Functionality

* Telegram bot receives messages.
* Daily Logs are appended to Google Sheets.
* Tasks are created and updated automatically.
* Existing Tasks are matched correctly.
* AI generates rolling task summaries.
* User confirmations work for uncertain matches.

---

## AI Features

* Entity extraction
* Task matching
* Status inference
* Tag generation
* Next-step extraction
* Summary generation

---

## User Experience

* Confirmation messages
* Search command
* Daily reminder
* Weekly summary
* Error recovery
* Helpful responses

---

## Engineering

* Automated tests
* Docker deployment
* GitHub Actions
* Logging
* Health checks
* Documentation

---

# 35. Implementation Roadmap

The recommended implementation sequence minimises dependencies and delivers usable functionality early.

---

## Phase 1 — Foundations

Estimated duration: **2–3 days**

Deliverables:

* Repository
* FastAPI
* Telegram Bot
* Google Sheets
* SQLite
* Docker
* CI/CD

Outcome:

A functioning backend with basic connectivity.

---

## Phase 2 — Core Logging

Estimated duration: **4–6 days**

Deliverables:

* Daily Log processing
* Task CRUD
* Repository layer
* Google Sheets updates
* Telegram confirmations

Outcome:

Users can record work through Telegram.

---

## Phase 3 — AI Intelligence

Estimated duration: **1–2 weeks**

Deliverables:

* Entity extraction
* Task matching
* Semantic search
* Summary generation
* Decision Engine
* Embeddings

Outcome:

The assistant understands work context and links updates intelligently.

---

## Phase 4 — Personalisation

Estimated duration: **1 week**

Deliverables:

* Alias learning
* Confidence adaptation
* Preferences
* AI memory
* Correction learning

Outcome:

The system becomes increasingly accurate for the individual user.

---

## Phase 5 — Productivity Features

Estimated duration: **1 week**

Deliverables:

* Weekly summaries
* Monthly reports
* Search improvements
* Reminder scheduler

Outcome:

The assistant evolves from a logger into a productivity companion.

---

## Phase 6 — Portfolio Polish

Estimated duration: **1 week**

Deliverables:

* Complete documentation
* Architecture diagrams
* README
* Demo video
* Example dataset
* Screenshots
* Deployment guide

Outcome:

A polished, production-quality portfolio project suitable for interviews and GitHub.

---

# 36. Future Migration Plan

The architecture supports incremental evolution without major refactoring.

Suggested progression:

```text id="2g5vfm"
MVP

↓

Google Sheets
+
SQLite

↓

PostgreSQL

↓

Vector Database

↓

Neo4j

↓

GraphRAG

↓

Multi-Agent System

↓

Web Dashboard

↓

Multi-User SaaS
```

Each migration should preserve existing application interfaces.

---

# 37. Final Thoughts

WorkGraph AI is intentionally designed as more than a simple Telegram logging bot.

It demonstrates several modern software engineering concepts:

* Clean Architecture
* Repository Pattern
* Domain-Driven Design
* AI orchestration
* Semantic search
* Human-in-the-loop decision making
* Background processing
* Provider-agnostic AI integration
* Scalable system design

The MVP delivers immediate practical value while providing a strong foundation for future capabilities such as GraphRAG, autonomous AI agents and enterprise knowledge management.

By following this implementation guide alongside the PRD, Architecture and AI Design documents, a developer should be able to build a maintainable, extensible and production-ready system that serves both as a daily productivity tool and as a compelling portfolio project demonstrating end-to-end AI application engineering.

---

# Part 4 Summary

This final section completes the implementation guide by covering the operational aspects of the project:

* A comprehensive testing strategy for both deterministic logic and AI behaviour.
* Structured logging, monitoring and deployment practices.
* CI/CD automation and operational readiness.
* Performance optimisation and security recommendations.
* A phased implementation roadmap from MVP to advanced AI capabilities.
* A clear migration path toward future technologies such as PostgreSQL, vector databases, GraphRAG and multi-agent systems.

Together with the PRD, Architecture and AI Design documents, this guide forms a complete blueprint for building, operating and evolving WorkGraph AI from an initial personal assistant into a sophisticated AI-powered work intelligence platform.
