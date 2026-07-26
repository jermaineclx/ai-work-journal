# WorkGraph AI

# Architecture Design Document

**Document Version:** 1.0 (Draft)
**Status:** Architecture Design – Phase 1 (MVP)
**Related Documents:**

* `01_PRD.md`
* `03_AI_DESIGN.md`
* `04_IMPLEMENTATION.md`

---

# 1. Introduction

## Purpose

This document describes the technical architecture of **WorkGraph AI**, including the major system components, architectural principles, communication patterns and engineering decisions that guide implementation.

Unlike the Product Requirements Document (PRD), which focuses on **what** the product should do, this document focuses on **how** those requirements will be implemented.

The architecture is intentionally designed to support incremental evolution—from a lightweight Telegram work logger to an AI-powered professional knowledge platform—without requiring major architectural rewrites.

---

## Scope

This document covers the architecture for the MVP as well as architectural considerations for future expansion.

It includes:

* High-level system architecture
* Component responsibilities
* Service boundaries
* Communication patterns
* Architectural principles
* Technology selection rationale

The following topics are covered in separate documents:

* Prompt engineering (`AI_DESIGN.md`)
* API specifications (`API_SPEC.md`)
* Database schema (`DATABASE.md`)
* Implementation plan (`IMPLEMENTATION.md`)

---

# 2. Architectural Goals

Every architectural decision should satisfy one or more of the following goals.

---

## Goal 1 — Minimise User Friction

The architecture should optimise for the fastest possible user interaction.

The user's workflow should consist of:

```text
Think

↓

Send Telegram message

↓

Receive confirmation
```

Everything else should happen automatically.

---

## Goal 2 — AI as a Service, Not the System

The Large Language Model should **assist** the application rather than become the application.

Business rules must never exist solely inside prompts.

Instead:

```text
Application Logic

↓

AI Assistance

↓

Structured Decision

↓

Persistence
```

This separation ensures:

* deterministic behaviour
* easier testing
* easier debugging
* provider independence

---

## Goal 3 — Loose Coupling

Each component should have a clearly defined responsibility.

Changing one component should have minimal impact on others.

Examples:

Changing OpenAI

↓

Should NOT affect

* Telegram
* Google Sheets
* APIs
* Business Logic

Changing Google Sheets

↓

Should NOT affect

* AI
* Telegram
* Search
* Task Matching

---

## Goal 4 — Incremental Evolution

The MVP should remain intentionally simple while allowing significant future expansion.

For example:

MVP

```text
Google Sheets
```

Future

```text
PostgreSQL

+

Neo4j

+

Vector Database
```

without changing application behaviour.

---

## Goal 5 — Human-Centred AI

The architecture should always favour explainability and user control over maximum automation.

The AI recommends.

The user confirms.

This philosophy influences:

* service boundaries
* confirmation workflow
* confidence scoring
* audit logging

---

# 3. Design Principles

The architecture follows several engineering principles that guide implementation.

---

## Principle 1 — Single Responsibility

Every service should perform one primary responsibility.

Examples:

Extraction Service

↓

Extract structured information

NOT

* update spreadsheets
* send Telegram messages
* generate summaries

Similarly,

Summary Service

↓

Generate summaries

NOT

* classify tasks
* create embeddings
* write to storage

---

## Principle 2 — Layered Architecture

Business logic should be isolated from infrastructure.

```text
Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer
```

This separation makes the system easier to maintain and test.

---

## Principle 3 — Infrastructure Independence

Infrastructure should support the application rather than define it.

Examples:

Storage may change.

Messaging platform may change.

LLM provider may change.

The application should continue functioning with minimal modifications.

---

## Principle 4 — AI-Augmented Decision Making

Artificial Intelligence provides recommendations.

Business Logic determines:

* whether recommendations are accepted
* whether confirmation is required
* whether additional processing occurs

The LLM should never directly modify persistent data.

---

## Principle 5 — Observable Systems

Every significant operation should be measurable.

Examples include:

* latency
* confidence
* token usage
* failures
* retries
* API duration

This enables future optimisation and debugging.

---

# 4. High-Level System Architecture

## Overview

WorkGraph AI follows a layered service architecture.

Each layer has a clearly defined responsibility.

```text
                     User
                      │
                      ▼
              Telegram Bot
                      │
                      ▼
                API Gateway
                      │
                      ▼
            Application Services
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 AI Services     Task Services    Search Services
      │               │                │
      └───────────────┼────────────────┘
                      ▼
             Decision Engine
                      │
      ┌───────────────┼────────────────┐
      ▼                                ▼
 Google Sheets                    SQLite
(User Records)                  (AI Memory)
```

---

## Layer Responsibilities

| Layer          | Responsibility                      |
| -------------- | ----------------------------------- |
| Presentation   | Telegram user interaction           |
| API            | Authentication, routing, validation |
| Application    | Workflow orchestration              |
| AI             | Language understanding              |
| Domain         | Business rules                      |
| Persistence    | Data storage                        |
| Infrastructure | External integrations               |

Each layer communicates only with adjacent layers.

---

## Why Layered Architecture?

The layered approach provides several advantages.

### Easier Testing

AI services can be tested independently.

Business rules can be tested without calling the LLM.

---

### Easier Maintenance

Replacing Google Sheets does not affect Telegram.

Replacing Telegram does not affect Task Matching.

Replacing OpenAI does not affect APIs.

---

### Future Scalability

Additional interfaces such as:

* Web
* Mobile
* Slack
* SeaTalk

can reuse the same Application Layer.

---

# 5. Component Architecture

This section describes each major system component and its responsibilities.

---

# 5.1 Presentation Layer

## Purpose

The Presentation Layer handles all user interactions.

For the MVP this consists exclusively of a Telegram Bot.

Future interfaces should reuse the same backend services.

---

## Responsibilities

* receive messages
* display confirmations
* present search results
* collect user corrections
* display summaries

The Presentation Layer contains **no business logic**.

---

## Design Philosophy

Telegram is treated as a thin client.

It should simply display information and relay user input.

All intelligence resides inside backend services.

---

## Future Interfaces

The architecture supports future additions such as:

* Web Dashboard
* Mobile Application
* SeaTalk Bot
* Slack Bot
* Microsoft Teams Bot

without modifying business logic.

---

# 5.2 API Layer

## Purpose

The API Layer acts as the entry point into the backend.

Every request passes through this layer before reaching application services.

---

## Responsibilities

* authentication
* validation
* routing
* request parsing
* response formatting
* error handling

The API Layer should remain stateless.

---

## Example Flow

```text
Telegram

↓

POST /log

↓

Validate Request

↓

Application Service
```

---

## Why Separate an API Layer?

Separating the API from business logic provides:

* reusable endpoints
* cleaner testing
* interface independence
* easier future integrations

---

# 5.3 Application Layer

## Purpose

The Application Layer coordinates the complete workflow.

It determines:

* which services execute
* execution order
* confirmation requirements
* persistence behaviour

This layer contains orchestration rather than business logic.

---

## Responsibilities

Examples include:

Process Daily Log

↓

Extract Information

↓

Find Task

↓

Calculate Confidence

↓

Determine User Interaction

↓

Save Records

---

The Application Layer does **not**:

* call Google Sheets directly
* implement extraction prompts
* perform similarity calculations

Those responsibilities belong elsewhere.

---

# 5.4 AI Layer

## Purpose

The AI Layer converts natural language into structured professional knowledge.

Rather than using one monolithic prompt, WorkGraph AI decomposes AI behaviour into specialised services.

This improves:

* maintainability
* explainability
* evaluation
* future model upgrades

---

## AI Service Architecture

```text
Incoming Message

↓

Extraction Service

↓

Task Matching Service

↓

Status Classification Service

↓

Summary Service

↓

Decision Engine
```

Each service has a single responsibility.

---

## AI Responsibilities

The AI Layer performs:

* entity extraction
* stakeholder detection
* task matching
* tag generation
* status inference
* next-step detection
* summary generation

The AI Layer **never writes directly to storage**.

---

# 5.5 Domain Layer

## Purpose

The Domain Layer represents the core business logic of WorkGraph AI.

Unlike the AI Layer, the Domain Layer is deterministic.

It contains the rules that define how the application behaves regardless of which AI provider is used.

---

## Responsibilities

Examples include:

* confidence thresholds
* task creation rules
* duplicate prevention
* confirmation workflow
* task lifecycle
* status transitions
* validation rules

These rules should remain stable even if the underlying language model changes.

---

## Example

AI Output

```json
{
  "task": "Settlement Reconciliation",
  "confidence": 0.87
}
```

Domain Logic

```text
Confidence = 87%

↓

Require User Confirmation

↓

Wait for Response

↓

Persist if Approved
```

The decision belongs to the Domain Layer, not the AI.

---

# 5.6 Infrastructure Layer

## Purpose

The Infrastructure Layer provides integrations with external systems.

It abstracts implementation details away from the rest of the application.

---

## Initial Components

### Telegram API

Responsible for:

* receiving messages
* sending replies
* handling callbacks

---

### Google Sheets API

Responsible for:

* reading Tasks
* writing Daily Logs
* updating summaries
* retrieving historical records

---

### SQLite

Used as lightweight internal storage for AI-specific metadata.

Examples include:

* learned abbreviations
* user preferences
* cached embeddings
* confidence history
* interaction statistics

This separation ensures Google Sheets remains the human-readable record while SQLite supports AI capabilities.

---

### LLM Provider

The architecture assumes a provider-agnostic interface.

The backend communicates with an abstraction layer rather than a specific vendor SDK.

Benefits include:

* easy provider switching
* A/B model testing
* fallback models
* reduced vendor lock-in

Supported providers may include:

* OpenAI
* Google Gemini
* Anthropic Claude
* Future local models

---

# Part 1 Summary

At the end of Part 1, the architecture establishes several important principles:

* A **layered architecture** separates concerns and simplifies maintenance.
* The **LLM is treated as an intelligent service**, not as the application itself.
* **Business logic remains deterministic** and independent of AI providers.
* **Google Sheets serves as the user-facing source of truth**, while **SQLite stores AI-specific metadata** to enable future personalisation.
* Every component has a clearly defined responsibility, making the system easier to test, extend and evolve.

These decisions provide a solid foundation for future enhancements while keeping the MVP intentionally lightweight and maintainable.


# 6. Request Lifecycle

## Overview

Every interaction in WorkGraph AI follows a deterministic processing pipeline. Regardless of the user's message content, the application executes the same high-level workflow, ensuring consistent behaviour and simplifying debugging.

The primary design objective is to separate **AI reasoning**, **business decisions**, and **data persistence** into distinct stages.

---

## High-Level Lifecycle

```text
User

↓

Telegram Bot

↓

FastAPI Endpoint

↓

Request Validation

↓

Application Service

↓

AI Pipeline

↓

Decision Engine

↓

Persistence Layer

↓

Telegram Response
```

Each stage has a single responsibility and communicates only with adjacent layers.

---

# Lifecycle Walkthrough

## Step 1 — User Sends a Message

Example:

> Finished the settlement SQL today. Finance approved it. QA tomorrow.

Telegram delivers the webhook request to the backend.

Responsibilities:

* receive message
* identify user
* capture timestamp
* assign request ID
* acknowledge receipt

Example request object:

```json
{
    "user_id": "telegram_12345",
    "message": "Finished the settlement SQL today. Finance approved it.",
    "timestamp": "2026-07-26T18:42:15+08:00"
}
```

At this point the message remains completely unstructured.

---

## Step 2 — API Validation

The API Layer validates:

* request format
* authentication
* webhook signature
* message length
* supported message type

Invalid requests terminate immediately.

Example:

```text
Missing message

↓

400 Bad Request
```

The API Layer never performs AI reasoning.

---

## Step 3 — Application Service

The Application Service becomes the workflow coordinator.

Responsibilities:

* initialise processing context
* load user configuration
* create processing session
* invoke AI pipeline
* collect AI outputs
* call Decision Engine
* coordinate persistence

No business decisions occur here.

---

## Step 4 — AI Pipeline

The user's message enters the AI processing pipeline.

```text
Raw Message

↓

Extraction

↓

Task Matching

↓

Status Classification

↓

Resource Detection

↓

Tag Generation

↓

Summary Generation
```

Each AI component returns structured output.

Example:

```json
{
    "stakeholder": "Finance",
    "status": "Waiting QA",
    "next_step": "QA tomorrow",
    "resources": [],
    "confidence": 0.91
}
```

Importantly:

Each AI service operates independently.

No service modifies persistent storage.

---

## Step 5 — Decision Engine

The Decision Engine receives structured AI outputs.

Its responsibility is to answer:

Should this be saved?

Should confirmation be requested?

Should a new task be created?

Should existing tasks be updated?

Unlike the AI Layer, this logic is entirely deterministic.

---

## Step 6 — Persistence

After the Decision Engine approves an action:

Application Services call Repository classes.

Repositories update:

* Google Sheets
* SQLite

The AI Layer never interacts directly with storage.

---

## Step 7 — User Feedback

Finally:

Telegram receives a concise response.

Example:

```text
✓ Logged successfully

Task:
Settlement Reconciliation

Status:
Waiting QA

Timeline updated.
```

The interaction ends.

---

# Processing States

Every request moves through a finite state machine.

```text
Received

↓

Validated

↓

Processing

↓

Decision

↓

Persisting

↓

Completed
```

Failure states are discussed later in this document.

---

# Request Context

Throughout processing, a shared Request Context object is maintained.

Example

```python
RequestContext

├── request_id
├── user_id
├── timestamp
├── original_message
├── ai_outputs
├── matched_task
├── confidence
├── final_decision
└── execution_time
```

The Request Context exists only during request processing.

It is not permanent storage.

---

# Idempotency

Repeated webhook deliveries should not create duplicate Daily Logs.

Each request should receive an internal Request ID.

Before persistence, the repository checks whether the request has already been processed.

Example:

```text
Telegram Retry

↓

Existing Request ID?

↓

Yes

↓

Return Previous Result
```

This prevents duplicate entries caused by network retries.

---

# 7. AI Processing Pipeline

## Philosophy

Rather than relying on one large prompt, WorkGraph AI decomposes AI reasoning into specialised services.

Advantages:

* easier testing
* lower maintenance
* clearer evaluation
* prompt independence
* future model flexibility

---

## Pipeline Overview

```text
Raw Message

↓

Pre-processing

↓

Entity Extraction

↓

Task Matching

↓

Status Classification

↓

Resource Detection

↓

Tag Generation

↓

Summary Update

↓

Decision Engine
```

Each stage enriches the message before passing it onwards.

---

# Stage 1 — Pre-processing

Responsibilities:

* remove unnecessary whitespace
* standardise dates
* detect URLs
* detect code blocks
* normalise formatting

Example

Input

```text
worked on settlement sql today
```

Output

```text
Worked on settlement SQL today.
```

No semantic interpretation occurs yet.

---

# Stage 2 — Entity Extraction

Purpose:

Convert natural language into structured information.

Extracted entities include:

* stakeholder
* task
* dates
* resources
* next steps
* deliverables

Example

Input

> Finance approved dashboard.

Output

```json
{
    "stakeholder":"Finance",
    "task":"Dashboard",
    "status":"Completed"
}
```

---

# Stage 3 — Task Matching

The Task Matching Service searches existing Tasks.

Inputs:

* extracted entities
* task summaries
* historical updates
* stakeholder
* learned aliases

Outputs:

```json
{
    "matched_task":"Settlement Reconciliation",
    "confidence":0.94
}
```

No persistence occurs.

---

# Stage 4 — Status Classification

Purpose:

Infer task progress.

Possible statuses include:

* Not Started
* In Progress
* Waiting Feedback
* Waiting QA
* Blocked
* Completed

Classification uses:

* extracted entities
* historical task state
* semantic cues

---

# Stage 5 — Resource Detection

Resources enrich work history.

Examples:

* DataSuite dashboard
* SQL script
* Google Sheet
* SeaTalk thread
* Documentation

Future integrations may automatically fetch metadata.

---

# Stage 6 — Tag Generation

Tags improve discoverability.

Examples

```text
SQL

Dashboard

Automation

Meeting

Experiment

Finance
```

Tags remain editable.

---

# Stage 7 — Summary Update

Rather than appending text, summaries should be rewritten to reflect current project state.

Poor summary

```text
Worked on SQL.

Worked on SQL.

Worked on SQL.
```

Desired summary

```text
Settlement SQL completed.

Finance approved the implementation.

Currently awaiting QA.
```

---

# AI Pipeline Outputs

The pipeline returns one consolidated object.

```json
{
    "entities": {},
    "matched_task": {},
    "status": {},
    "resources": [],
    "tags": [],
    "summary": "",
    "confidence": 0.91
}
```

This object becomes input for the Decision Engine.

---

# 8. Data Flow

## Overview

Data flows through WorkGraph AI in one direction.

The AI never writes directly to storage.

```text
Telegram

↓

API

↓

Application

↓

AI

↓

Decision Engine

↓

Repositories

↓

Storage
```

---

## Why One-Way Data Flow?

Benefits include:

* easier debugging
* deterministic execution
* simpler testing
* fewer circular dependencies

---

# Storage Responsibilities

Google Sheets stores:

* Tasks
* Daily Logs

SQLite stores:

* learned aliases
* embeddings
* confidence history
* cached summaries
* user preferences

This separation keeps Google Sheets human-readable.

---

# Reading Data

Repositories expose methods such as:

```text
get_tasks()

get_daily_logs()

get_task(task_id)

save_log()

update_task()
```

Application Services never communicate directly with Google APIs.

---

# Writing Data

Repositories determine:

* write order
* retries
* transaction behaviour
* duplicate detection

Business Logic never manages spreadsheet updates directly.

---

# Caching Strategy

Frequently accessed data may be cached.

Examples:

* active tasks
* embeddings
* stakeholder aliases
* recent summaries

Caching reduces API calls while improving latency.

---

# Synchronisation

Google Sheets remains the user-facing source of truth.

SQLite stores AI metadata.

Both stores should remain synchronised after every successful request.

Future migrations should preserve this abstraction.

---

# 9. Service Responsibilities

## Overview

Each service owns one clearly defined responsibility.

Services communicate through interfaces rather than direct implementation details.

---

# Telegram Service

Responsibilities

* receive messages
* send replies
* handle callback buttons

Does not:

* perform AI reasoning
* access databases
* determine business rules

---

# Application Service

Responsibilities

* orchestrate workflow
* manage request context
* coordinate services

Does not:

* extract entities
* perform storage operations

---

# Extraction Service

Responsibilities

* identify structured information
* produce extracted entities

Does not:

* match tasks
* generate summaries

---

# Task Matching Service

Responsibilities

* semantic matching
* similarity scoring
* duplicate detection

Does not:

* update tasks
* write spreadsheets

---

# Summary Service

Responsibilities

* update task summaries
* generate weekly summaries

Does not:

* classify stakeholders
* determine persistence

---

# Decision Engine

Responsibilities

* evaluate confidence
* determine confirmation workflow
* decide persistence actions

The Decision Engine represents the bridge between probabilistic AI outputs and deterministic application behaviour.

---

# Repository Layer

Responsibilities

* read storage
* update storage
* retry failed writes
* enforce persistence contracts

Repositories isolate infrastructure from business logic.

---

# LLM Provider

Responsibilities

* language understanding
* extraction
* reasoning
* summarisation

The provider is hidden behind an interface so that changing models does not affect the rest of the application.

---

# Communication Contracts

All services communicate using strongly defined request and response models.

Example:

```text
Application Service

↓

ExtractionRequest

↓

Extraction Service

↓

ExtractionResponse

↓

Application Service
```

This avoids leaking internal implementation details between services.

---

# Dependency Direction

Dependencies always point inward.

```text
Telegram

↓

API

↓

Application

↓

Domain

↓

Repositories

↓

Infrastructure
```

Higher-level modules should never depend directly on lower-level implementation details.

This follows the Dependency Inversion Principle and makes future refactoring significantly easier.

---

# Part 2 Summary

This section defines how WorkGraph AI behaves at runtime.

Key architectural decisions include:

* A deterministic request lifecycle orchestrated by the Application Layer.
* A modular AI pipeline composed of specialised services with single responsibilities.
* A one-way data flow that separates AI reasoning from persistence.
* Repository abstractions that isolate infrastructure concerns from business logic.
* Clear communication contracts between services to support testing, maintainability and future extensibility.

By separating orchestration, AI reasoning, business decisions and storage, the architecture remains flexible enough to support future enhancements—such as new interfaces, storage backends or AI providers—without requiring fundamental changes to the core application structure.


# 10. Project Structure

## Overview

The project follows a **Clean Architecture** approach combined with **Domain-Driven Design (DDD)** principles. Business logic remains independent of frameworks, databases and AI providers.

The directory structure is organised around responsibilities rather than technologies.

```text
workgraph-ai/

├── app/
│   ├── api/
│   ├── core/
│   ├── domain/
│   ├── services/
│   ├── ai/
│   ├── repositories/
│   ├── integrations/
│   ├── models/
│   ├── schemas/
│   ├── prompts/
│   ├── memory/
│   ├── utils/
│   └── config/
│
├── tests/
│
├── scripts/
│
├── docs/
│
├── docker/
│
├── .github/
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Directory Responsibilities

## `/api`

Contains FastAPI routers.

Responsibilities:

* HTTP endpoints
* Telegram webhook
* request validation
* response formatting

Should contain **no business logic**.

---

## `/core`

Shared application infrastructure.

Examples:

* dependency injection
* logging
* configuration
* exception handling
* middleware

---

## `/domain`

Represents the business domain.

Contains:

* entities
* enums
* business rules
* validation logic
* domain services

The Domain Layer must remain framework-independent.

---

## `/services`

Application orchestration.

Examples:

* LogService
* TaskService
* SearchService
* SummaryService

Services coordinate workflows but avoid infrastructure concerns.

---

## `/ai`

Contains all AI-specific functionality.

Subdirectories:

```text
ai/

├── extraction/
├── matching/
├── classification/
├── summarisation/
├── embeddings/
├── evaluation/
└── providers/
```

Each AI capability is isolated into its own module.

---

## `/repositories`

Persistence abstraction.

Repositories hide storage implementation details.

Example:

```text
TaskRepository

↓

Google Sheets

(SQLite later)
```

Future migrations require changing repositories rather than application logic.

---

## `/integrations`

External services.

Examples:

* Telegram
* Google Sheets
* OpenAI
* Gemini

Each integration should expose a clean interface.

---

## `/memory`

Stores AI-specific metadata.

Examples:

* learned aliases
* embeddings
* cached summaries
* interaction history
* confidence statistics

This directory should not contain user-facing business data.

---

## `/prompts`

Prompt templates are treated as first-class assets.

Example:

```text
prompts/

extract_entities.md

match_task.md

generate_summary.md

weekly_report.md
```

Prompt versioning allows experimentation without affecting application logic.

---

# 11. Database Architecture

## Philosophy

The MVP intentionally separates **business records** from **AI memory**.

This distinction is one of the most important architectural decisions in WorkGraph AI.

Business records answer:

> What happened?

AI memory answers:

> How does the AI become smarter?

These are fundamentally different responsibilities.

---

# High-Level Architecture

```text
                Application

                     │

      ┌──────────────┴──────────────┐

      ▼                             ▼

Google Sheets                  SQLite

Business Records              AI Metadata
```

---

# Google Sheets

Google Sheets is the human-readable datastore.

Purpose:

* Tasks
* Daily Logs
* timelines
* summaries

Characteristics:

* editable
* exportable
* transparent
* auditable

Users should always understand what is stored.

---

# SQLite

SQLite is invisible to users.

Purpose:

* embeddings
* learned terminology
* confidence history
* cached LLM outputs
* AI preferences

SQLite exists solely to improve AI behaviour.

---

# Why Not Store Everything in Google Sheets?

Google Sheets is excellent for structured records.

It is less suitable for:

* embeddings
* vector similarity
* caching
* model metadata
* statistics

Separating these concerns simplifies future scaling.

---

# Future Database Evolution

The architecture intentionally allows gradual migration.

Phase 1

```text
Google Sheets

+

SQLite
```

↓

Phase 2

```text
PostgreSQL

+

SQLite
```

↓

Phase 3

```text
PostgreSQL

+

Vector Database

+

Neo4j
```

Application Services remain unchanged throughout these migrations.

---

# Repository Pattern

Repositories abstract storage.

Example:

```text
Application Service

↓

TaskRepository

↓

Google Sheets
```

Future

```text
Application Service

↓

TaskRepository

↓

PostgreSQL
```

Only the repository implementation changes.

---

# 12. Deployment Architecture

## Overview

The MVP targets simple cloud deployment with minimal operational overhead.

Recommended deployment platform:

* Railway

Alternative platforms:

* Render
* Fly.io
* Google Cloud Run

---

# Deployment Diagram

```text
                 Telegram

                     │

                     ▼

              Railway Deployment

                     │

        ┌────────────┼────────────┐

        ▼                         ▼

 FastAPI Backend            Background Jobs

        │

        ▼

 Google APIs + LLM APIs
```

---

# Backend Container

The backend runs inside a Docker container.

Responsibilities:

* FastAPI
* AI services
* repositories
* webhook handling

The container remains stateless.

Persistent information resides externally.

---

# Environment Variables

Configuration should never be hardcoded.

Examples:

```text
TELEGRAM_TOKEN

OPENAI_API_KEY

GOOGLE_SERVICE_ACCOUNT

DATABASE_URL

LOG_LEVEL
```

Secrets must never appear in Git history.

---

# CI/CD

Recommended pipeline:

```text
Git Push

↓

GitHub Actions

↓

Run Tests

↓

Build Docker Image

↓

Deploy Railway
```

Deployment should be fully automated.

---

# Backup Strategy

Google Sheets provides version history.

SQLite should be backed up regularly.

Recommended schedule:

* daily
* before deployment
* before schema migrations

---

# 13. Security Architecture

## Security Philosophy

Security should be built into the architecture rather than added later.

Even though the MVP is intended for personal use, professional work records may contain confidential business information.

---

# Authentication

The MVP assumes:

One user

↓

One Telegram account

↓

One backend

Future versions may support:

* OAuth
* SSO
* Enterprise Identity Providers

---

# Authorisation

Current permissions:

Owner

↓

Full Access

Future:

```text
Admin

Manager

User

Viewer
```

---

# Secrets Management

Secrets include:

* Telegram Token
* OpenAI Key
* Google Credentials

Requirements:

* environment variables
* encrypted storage
* rotation support

Secrets must never be committed.

---

# Data Protection

Sensitive data should be protected during:

Transmission

↓

HTTPS

Storage

↓

encrypted credentials

Logging

↓

minimal exposure

---

# Prompt Injection Protection

Future AI improvements should consider:

* malicious URLs
* prompt injection
* prompt leakage
* tool misuse

The application should sanitise user input before AI processing where appropriate.

---

# Rate Limiting

Recommended protections:

* webhook throttling
* request limits
* retry delays

These reduce accidental abuse.

---

# 14. Scalability

## MVP Philosophy

The MVP intentionally prioritises developer velocity over horizontal scalability.

However, architectural decisions should avoid creating unnecessary migration barriers.

---

# Horizontal Scaling

Stateless services enable multiple backend instances.

```text
Telegram

↓

Load Balancer

↓

Backend A

Backend B

Backend C
```

---

# AI Scaling

Future optimisation options:

* batching
* response caching
* asynchronous inference
* multiple providers
* fallback models

---

# Storage Scaling

Current:

Google Sheets

↓

Future:

PostgreSQL

↓

Partitioning

↓

Read Replicas

---

# Search Scaling

Current:

Semantic matching

↓

Future:

Dedicated Vector Database

Examples:

* pgvector
* Pinecone
* Weaviate
* Qdrant

---

# Knowledge Graph Scaling

Future architecture introduces:

Neo4j

↓

GraphRAG

↓

Hybrid Search

↓

Reasoning Engine

without modifying higher-level services.

---

# 15. Observability

## Philosophy

AI systems require significantly more observability than traditional CRUD applications.

Understanding *why* an AI decision was made is just as important as whether it succeeded.

---

# Logging

Recommended structured logs:

```text
Timestamp

User

Request ID

Latency

Prompt Version

LLM Provider

Confidence

Decision

Storage Result
```

Logs should support debugging while minimising exposure of sensitive user content.

---

# Metrics

Suggested metrics:

Performance

* request latency
* AI latency
* Google API latency

Usage

* logs per day
* active tasks
* searches

Quality

* task matching accuracy
* correction rate
* confirmation rate

Cost

* token usage
* API spend
* average request cost

---

# Health Checks

Expose endpoints:

```text
/health

/ready

/version
```

Health checks should verify:

* Google connectivity
* Telegram connectivity
* LLM provider availability

---

# Monitoring Dashboard

Future dashboard may include:

* request volume
* error rate
* confidence distribution
* latency
* cost trends

This assists optimisation and operational monitoring.

---

# 16. Architecture Decision Records (ADRs)

## ADR-001

### Decision

Use Telegram as the primary interface.

### Rationale

* already installed
* mobile-first
* conversational
* minimal friction

Alternative:

Dedicated web application.

Rejected because it increases interaction cost during the MVP.

---

## ADR-002

### Decision

Use Google Sheets as the business datastore.

### Rationale

* transparent
* easy to inspect
* free
* minimal setup

Future migration remains straightforward.

---

## ADR-003

### Decision

Use SQLite for AI memory.

### Rationale

Separates AI metadata from business records.

Improves maintainability.

Enables embeddings without cluttering spreadsheets.

---

## ADR-004

### Decision

Adopt a provider-agnostic LLM interface.

### Rationale

Avoids vendor lock-in.

Supports experimentation.

Allows fallback providers.

---

## ADR-005

### Decision

Treat the LLM as an assistant rather than the source of business logic.

### Rationale

Improves determinism.

Supports testing.

Keeps application behaviour consistent across providers.

---

## ADR-006

### Decision

Require human confirmation for medium-confidence AI decisions.

### Rationale

Professional work records should prioritise correctness over automation.

---

# 17. Future Architecture

The architecture has been intentionally designed to evolve without significant restructuring.

Future additions include:

* Web dashboard
* Mobile application
* Voice logging
* Screenshot understanding
* Calendar integration
* SeaTalk integration
* GitHub integration
* PostgreSQL
* Vector database
* Neo4j
* GraphRAG
* Multi-user workspaces

All of these capabilities can be introduced by extending existing layers rather than redesigning the system.

---

# 18. Technology Stack

| Layer              | Technology                                             |
| ------------------ | ------------------------------------------------------ |
| Language           | Python 3.12+                                           |
| API Framework      | FastAPI                                                |
| Messaging          | Telegram Bot API                                       |
| AI Provider        | Provider-agnostic (OpenAI default)                     |
| Storage (Business) | Google Sheets API                                      |
| Storage (AI)       | SQLite                                                 |
| Semantic Search    | Embeddings (OpenAI `text-embedding-3-large` initially) |
| Deployment         | Railway                                                |
| Containerisation   | Docker                                                 |
| CI/CD              | GitHub Actions                                         |
| Logging            | Python Logging                                         |
| Testing            | Pytest                                                 |
| Configuration      | Pydantic Settings + `.env`                             |

---

# Part 3 Summary

The architecture intentionally separates **product data**, **AI reasoning**, and **infrastructure** into independent layers that can evolve over time.

Several design choices underpin this approach:

* Google Sheets remains the transparent, user-facing record of work.
* SQLite acts as a lightweight AI memory store for embeddings, preferences and learned metadata.
* Repository abstractions isolate storage technologies from application logic.
* Provider-agnostic AI interfaces reduce vendor lock-in and simplify experimentation.
* Clean Architecture principles ensure that business logic remains independent of frameworks, databases and external APIs.

This foundation supports the MVP while providing a clear migration path toward PostgreSQL, vector search, GraphRAG and multi-user deployments without requiring fundamental architectural changes.

