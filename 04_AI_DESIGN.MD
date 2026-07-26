# WorkGraph AI

# AI Design Document

**Document Version:** 1.0
**Status:** AI Design – MVP

**Related Documents**

* `01_PRD.md`
* `02_ARCHITECTURE.md`
* `04_IMPLEMENTATION.md`

---

# 1. Purpose

## Overview

This document describes the design of the Artificial Intelligence subsystem powering **WorkGraph AI**.

Unlike the Architecture document, which explains where AI fits into the system, this document focuses entirely on **how the AI reasons**, **what decisions it makes**, and **how prompts, memory and retrieval work together**.

The AI is designed around one philosophy:

> **AI should understand work, not replace judgement.**

The application always remains deterministic.

The AI recommends.

The user owns the final decision.

---

# Design Goals

The AI should:

* understand natural conversations
* identify existing work items
* remember project context
* generate concise professional summaries
* improve over time through user feedback
* remain explainable
* remain provider-independent

It should **not**:

* modify records without approval (unless confidence is extremely high)
* invent project details
* silently merge unrelated work
* become a black box

---

# Core Philosophy

The AI is composed of **specialised agents** coordinated by an orchestrator.

Rather than asking one enormous prompt to perform every task, WorkGraph AI decomposes reasoning into small, focused responsibilities.

Benefits:

* easier debugging
* lower prompt complexity
* easier evaluation
* modular upgrades
* agent replacement

---

# 2. AI System Overview

## Multi-Agent Architecture

```text id="6ng9gq"
                    User Message
                         │
                         ▼
                AI Orchestrator
                         │
 ┌─────────────┬──────────┼─────────────┬─────────────┐
 ▼             ▼          ▼             ▼             ▼
Extraction   Matcher   Status Agent   Tag Agent   Resource Agent
     │
     ▼
Summary Agent
     │
     ▼
Decision Engine
```

Each agent has one clearly defined objective.

Agents never communicate directly with storage.

---

# Why Agents Instead of One Prompt?

Suppose the user sends:

> Finished the settlement SQL. Finance approved it. QA tomorrow.

A monolithic prompt must simultaneously:

* extract stakeholders
* identify the task
* infer status
* determine next steps
* decide whether it matches an existing task
* update summaries

A specialised agent system separates these concerns.

Example:

Extraction Agent

↓

Produces structured entities

↓

Matching Agent

↓

Finds task

↓

Status Agent

↓

Determines progress

↓

Summary Agent

↓

Updates project summary

Each agent becomes easier to evaluate and improve independently.

---

# 3. AI Orchestrator

## Responsibilities

The AI Orchestrator coordinates every AI operation.

Responsibilities include:

* invoking agents
* managing execution order
* collecting outputs
* resolving conflicts
* returning one unified response

It should never contain prompt logic.

---

# Execution Pipeline

```text id="wj3m2f"
User Message

↓

Pre-processing

↓

Extraction Agent

↓

Task Matching Agent

↓

Status Agent

↓

Tag Agent

↓

Resource Agent

↓

Summary Agent

↓

Unified Output
```

---

# Unified Response

All agents contribute to a single object.

Example:

```json id="qz5goh"
{
  "task": "Settlement Reconciliation",
  "stakeholder": "Finance",
  "status": "Waiting QA",
  "summary": "Finance approved settlement SQL. QA scheduled tomorrow.",
  "next_steps": "Run QA",
  "tags": ["SQL", "Finance"],
  "confidence": 0.94
}
```

---

# 4. Agent Design

## 4.1 Extraction Agent

### Objective

Convert natural language into structured entities.

Extract:

* stakeholder
* task
* dates
* links
* resources
* next steps
* deliverables
* blockers

Example

Input:

> Discussed dashboard metrics with Product.

Output:

```json id="gb5hju"
{
  "stakeholder": "Product",
  "task": "Dashboard Metrics",
  "status": "In Progress"
}
```

---

## 4.2 Task Matching Agent

### Objective

Determine whether the update belongs to an existing task.

Inputs:

* extracted task
* embeddings
* summaries
* stakeholders
* aliases

Outputs:

* task ID
* similarity score
* confidence
* explanation

---

# Matching Pipeline

```text id="rz4v26"
Embedding Search

↓

Top 5 Candidates

↓

LLM Ranking

↓

Best Match
```

This hybrid approach balances speed with contextual understanding.

---

## 4.3 Status Agent

Objective:

Infer project state.

Supported statuses:

* Not Started
* In Progress
* Waiting Feedback
* Waiting QA
* Blocked
* Completed

Status should be inferred from language rather than keywords alone.

---

## 4.4 Tag Agent

Automatically generates tags.

Examples:

```text id="g80efj"
SQL

Dashboard

Automation

Meeting

Finance

Experiment
```

Tags improve future retrieval.

---

## 4.5 Resource Agent

Detects references to supporting artefacts.

Examples:

* DataSuite dashboard
* SQL script
* Google Sheet
* SeaTalk discussion
* Documentation
* File paths
* URLs

Future versions may retrieve metadata automatically.

---

## 4.6 Summary Agent

Maintains rolling task summaries.

Instead of appending text:

Bad

```text id="qyn3cm"
Worked on SQL.

Worked on SQL.

Worked on SQL.
```

Desired

```text id="a2ml6x"
Settlement SQL completed.

Finance approved implementation.

Awaiting QA.
```

Summaries should always reflect the current state.

---

# 5. Prompt Design

## Philosophy

Each prompt should perform exactly one task.

Avoid prompts that attempt to solve multiple unrelated problems.

---

# Prompt Structure

Every prompt contains:

1. System instructions
2. Objective
3. Available context
4. Required output schema
5. Examples
6. Validation instructions

---

## Example Layout

```text id="jkkzdu"
System

↓

Objective

↓

Context

↓

Instructions

↓

Examples

↓

JSON Output
```

---

# Output Constraints

Prompts should:

* return JSON only
* avoid markdown
* avoid explanations
* avoid speculative reasoning
* include confidence estimates where appropriate

---

# Few-Shot Examples

Each prompt should include representative examples.

Cover:

* meetings
* SQL work
* dashboards
* bug fixes
* investigations
* ambiguous updates

These examples improve consistency.

---

# 6. Retrieval-Augmented Generation (RAG)

## Why RAG?

The AI should reason using the user's actual work history rather than relying only on the language model.

---

# Context Sources

Available context includes:

* Tasks
* Daily Logs
* summaries
* stakeholder aliases
* learned abbreviations

---

# Retrieval Pipeline

```text id="rtjlwm"
Incoming Message

↓

Embedding

↓

Semantic Search

↓

Top Candidates

↓

Prompt Context

↓

LLM
```

Only the most relevant records should be injected into prompts.

---

# Context Window Strategy

Prioritise:

1. Current task
2. Recent updates
3. Stakeholder information
4. Similar historical tasks

Avoid sending the user's full work history.

---

# 7. Embeddings

## Purpose

Embeddings enable semantic understanding.

Each Task should have an embedding generated from:

* title
* summary
* stakeholder
* recent updates
* tags

---

# Embedding Refresh

Embeddings should be regenerated when:

* summaries change
* task titles change
* significant milestones occur

This is handled asynchronously.

---

# Storage

Embeddings are stored separately from business records.

Initially:

SQLite

Future:

pgvector

Pinecone

Weaviate

Qdrant

---

# 8. Memory System

## Philosophy

WorkGraph AI distinguishes between:

Business Memory

↓

What happened?

AI Memory

↓

How the AI should think.

---

# Short-Term Memory

Used during a request.

Contains:

* extracted entities
* candidate tasks
* intermediate reasoning

Discarded after completion.

---

# Long-Term Memory

Persists across sessions.

Examples:

* aliases
* abbreviations
* preferred terminology
* stakeholder mappings
* interaction history

Stored in SQLite.

---

# Learning Rules

The AI should only learn after explicit confirmation.

Example:

AI predicts:

Finance

↓

User corrects to:

Payments

↓

Store correction

↓

Improve future predictions

---

# 9. Confidence System

Confidence is calculated from multiple signals.

Suggested inputs:

* semantic similarity
* entity overlap
* stakeholder match
* historical behaviour
* LLM confidence

---

# Confidence Levels

|  Score | Behaviour  |
| -----: | ---------- |
|   ≥95% | Auto-apply |
| 80–94% | Confirm    |
|   <80% | Ask user   |

Confidence should never depend solely on the LLM.

---

# Explainability

Every decision should include an explanation.

Example:

```text id="hz81h7"
Matched

Settlement Reconciliation

Because:

• Same stakeholder

• Similar SQL keywords

• Similar historical summary
```

This improves trust.

---

# 10. Hallucination Prevention

The AI should never invent:

* stakeholders
* dates
* approvals
* project names
* links

Unknown values should remain null rather than fabricated.

---

# Validation Rules

Before persistence:

* required fields present
* confidence acceptable
* output schema valid
* task exists (if referenced)

Invalid outputs should trigger user clarification.

---

# 11. Prompt Evaluation

Every prompt should have:

* version number
* evaluation dataset
* quality metrics

Metrics:

* extraction accuracy
* matching accuracy
* summary quality
* correction rate

Prompt changes should always be benchmarked before deployment.

---

# 12. Future AI Roadmap

## Phase 1 — Current MVP

Capabilities:

* extraction
* matching
* summaries
* reminders

---

## Phase 2 — Personal AI

* adaptive terminology
* personalised confidence
* smarter reminders
* writing style learning

---

## Phase 3 — GraphRAG

Introduce:

Neo4j

↓

Knowledge Graph

↓

Relationship Search

Example:

```text id="vjlwm3"
Stakeholder

↓

Projects

↓

Meetings

↓

Deliverables
```

The AI begins reasoning over relationships rather than isolated records.

---

## Phase 4 — Agent Collaboration

Additional agents:

* Career Agent
* Performance Review Agent
* Weekly Planning Agent
* Meeting Preparation Agent
* Knowledge Discovery Agent

These agents reuse the same underlying work history.

---

## Phase 5 — Autonomous Work Assistant

Potential future capabilities:

* identify stalled tasks
* suggest priorities
* recommend follow-ups
* draft SeaTalk updates
* prepare meeting agendas
* generate monthly accomplishments
* identify recurring blockers
* highlight cross-project dependencies

The human remains in control of final actions.

---

# 13. AI Ethics & User Trust

The assistant should always:

* explain important decisions
* allow corrections
* preserve user ownership
* avoid hidden automation

Corrections should improve future behaviour without silently altering historical records.

---

# 14. Success Metrics

Technical metrics:

* extraction accuracy >95%
* task matching accuracy >90%
* confirmation rate decreases over time
* average latency <5 seconds
* summary regeneration success >99%

User metrics:

* daily logging becomes habitual
* reduced manual spreadsheet editing
* high trust in AI suggestions
* weekly summaries require minimal editing

---

# Final Summary

The AI subsystem of WorkGraph AI is built around a **multi-agent architecture** coordinated by an AI Orchestrator. Each specialised agent performs a focused reasoning task—such as entity extraction, task matching or summarisation—before handing structured outputs to the deterministic Decision Engine.

Retrieval-Augmented Generation (RAG), embeddings and a lightweight long-term memory allow the AI to reason using the user's own work history rather than relying solely on the language model. User-confirmed feedback continuously improves future predictions while preserving explainability and control.

This design keeps AI modular, testable and provider-independent, while establishing a clear path toward future enhancements including GraphRAG, collaborative agents and an autonomous work intelligence assistant.
