# WorkGraph AI

## Product Requirements Document (PRD)

**Version:** 1.0 (Draft)
**Status:** Draft – Phase 1 (MVP)
**Author:** Jermaine
**Last Updated:** 26 July 2026

---

# 1. Executive Summary

## Overview

WorkGraph AI is an AI-powered work intelligence platform that enables knowledge workers to effortlessly capture, organize, and retrieve their professional work history through natural language conversations.

Rather than requiring users to manually maintain spreadsheets, notebooks, project management tools or daily journals, WorkGraph AI transforms casual messages into structured knowledge. Users simply send updates through Telegram as if they were chatting with a colleague, while the system automatically extracts relevant information, associates updates with ongoing work, maintains project histories, and builds a long-term professional knowledge base.

The initial implementation focuses on Telegram and Google Sheets to minimise setup complexity and maximise accessibility. However, the long-term vision extends beyond a work logger into a personal AI career assistant capable of understanding professional history, generating reports, preparing performance reviews, and serving as an intelligent memory system.

---

## Vision Statement

> **WorkGraph AI helps professionals remember, understand, and leverage their work by transforming everyday conversations into structured professional knowledge.**

The product is built around a simple philosophy:

**People should spend their time doing meaningful work—not documenting it.**

---

## Product Summary

WorkGraph AI combines conversational AI, semantic search, intelligent task management and continuous learning into a single lightweight assistant.

Instead of filling forms such as:

* Date
* Stakeholder
* Project
* Status
* Links
* Next Steps

the user simply sends a message such as:

> Spent most of today investigating the settlement issue. Found duplicate joins in the SQL. Finance confirmed the numbers and we'll send it for QA tomorrow.

WorkGraph AI automatically understands:

* which task this belongs to
* who the stakeholder is
* current progress
* next actions
* related resources
* overall task timeline

before asking for confirmation where necessary.

---

## Target Audience

The initial target audience consists of individual knowledge workers whose work is spread across meetings, analysis, dashboards, documentation and stakeholder communication.

Examples include:

* Data Analysts
* Business Analysts
* Data Scientists
* Analytics Engineers
* Machine Learning Engineers
* Software Engineers
* Product Managers
* Consultants
* Researchers

Although the first release targets individual users, the architecture should allow future expansion into team-based and enterprise environments.

---

## Why This Product Exists

Modern knowledge work produces valuable information every day, yet very little of it is intentionally preserved.

Professionals frequently forget:

* what they worked on
* when work was completed
* who requested it
* which stakeholders were involved
* what problems were solved
* what business impact was achieved

This creates challenges during:

* performance reviews
* promotion discussions
* resume writing
* interview preparation
* quarterly reporting
* project retrospectives
* knowledge transfer

Most existing tools require users to interrupt their workflow and manually organise information. As a result, documentation is often postponed until important details have already been forgotten.

WorkGraph AI removes this friction by integrating directly into a communication channel that users already access throughout the day.

---

## Core Value Proposition

WorkGraph AI provides four primary benefits.

### Effortless Capture

Users describe work naturally.

The AI performs the administrative work.

---

### Intelligent Organisation

Rather than storing isolated notes, the system automatically groups updates into ongoing tasks, creating a living timeline of professional work.

---

### Searchable Professional Memory

Months later, users should be able to ask questions such as:

> What did I work on for Finance in March?

or

> Which dashboards did I build this quarter?

without manually searching through notes or spreadsheets.

---

### Career Intelligence

Over time, the system transforms historical work into useful career assets, including summaries, accomplishment reports and promotion evidence.

These capabilities are considered future phases of the product and are intentionally separated from the MVP.

---

# 2. Problem Statement

## Background

Knowledge workers spend considerable time solving problems, collaborating with stakeholders and delivering business value.

Ironically, documenting these achievements often receives little attention despite its importance.

This creates an imbalance:

* Significant effort is invested into producing work.
* Minimal effort is invested into preserving work.

The consequences become apparent months later when users struggle to reconstruct their own contributions.

---

## Existing Workflow

A typical workflow today resembles the following:

```text
Receive request

↓

Work on analysis

↓

Meeting

↓

SQL

↓

Dashboard

↓

Stakeholder feedback

↓

Deployment

↓

Move on
```

Documentation, if it occurs at all, is usually delayed until:

* weekly reports
* performance review season
* resume updates
* interview preparation

By then, many details have already been forgotten.

---

## Existing Solutions

Several categories of tools attempt to address this problem.

### Note-taking Applications

Examples include digital notebooks and personal knowledge management systems.

Strengths:

* flexible
* searchable

Weaknesses:

* require manual organisation
* quickly become cluttered
* little understanding of relationships between work items

---

### Project Management Tools

Examples include ticketing systems and task boards.

Strengths:

* structured
* collaborative

Weaknesses:

* designed around tickets rather than evolving work
* significant manual maintenance
* often disconnected from daily thought processes

---

### Spreadsheets

Many professionals maintain personal work logs in spreadsheets.

Strengths:

* flexible
* familiar

Weaknesses:

* repetitive manual entry
* poor user experience
* difficult to maintain consistently

---

### Daily Journals

Personal journals capture chronological history.

Strengths:

* natural writing experience

Weaknesses:

* weak search capabilities
* no task relationships
* no structured analytics

---

## Key Problems

### Problem 1 — High Logging Friction

Capturing work requires opening another application, remembering relevant details and completing multiple fields.

Even small amounts of friction significantly reduce long-term adoption.

---

### Problem 2 — Loss of Context

Updates become isolated records rather than connected histories.

Users remember individual events but struggle to reconstruct complete project timelines.

---

### Problem 3 — Fragmented Information

Relevant information exists across multiple sources:

* conversations
* dashboards
* SQL queries
* documents
* spreadsheets
* personal memory

There is no single location that connects these together.

---

### Problem 4 — Poor Retrieval

Users often remember solving a problem but cannot remember:

* when
* for whom
* under which project
* using which resources

Keyword search is often insufficient.

---

### Problem 5 — Career Knowledge Decay

Every forgotten accomplishment represents lost professional value.

This affects:

* resume quality
* interview performance
* promotion evidence
* annual reviews

---

## Opportunity

Recent advances in Large Language Models create an opportunity to fundamentally change how work is documented.

Instead of requiring users to manually structure information, AI can now:

* understand natural language
* identify entities
* recognise relationships
* infer context
* organise knowledge automatically

This enables documentation to become conversational rather than administrative.

---

# 3. Product Vision

## Long-Term Vision

WorkGraph AI aims to become the user's professional memory.

Rather than acting as another productivity tool, it should function as an intelligent companion that continuously captures, understands and organises professional work throughout a user's career.

Over time, the system should evolve from a work logger into an AI-powered career intelligence platform.

---

## Product Mission

**To eliminate the administrative burden of documenting work while ensuring that valuable professional knowledge is never lost.**

---

## Design Philosophy

Three principles guide every design decision.

### Capture Once

Users should never need to repeat information.

Information should be captured once and reused throughout the system.

---

### Organise Automatically

The responsibility for structuring information belongs to the AI rather than the user.

Users communicate naturally.

The system creates structure.

---

### Preserve Forever

Professional work represents accumulated experience.

The platform should preserve this knowledge so that it remains accessible years later.

---

## Success Criteria

The MVP will be considered successful if it consistently achieves the following outcomes:

### User Experience

* Logging work takes less than 30 seconds.
* Users rarely open Google Sheets directly.
* Logging feels as natural as sending a chat message.

---

### AI Performance

* Correct task matching exceeds 90% after confirmation.
* Status detection requires minimal editing.
* New task detection is accurate and predictable.

---

### Product Adoption

* Daily usage becomes habitual.
* Historical work can be retrieved quickly.
* Users trust AI suggestions while remaining in control.

---

# 4. Product Goals

## Primary Goal

Reduce the effort required to maintain an accurate professional work history.

The system should remove repetitive administrative tasks while preserving high-quality records.

---

## Secondary Goals

### Build Task Histories

Transform isolated daily updates into connected timelines.

---

### Improve Information Retrieval

Enable users to retrieve historical work through natural language rather than manual searching.

---

### Create a Reliable Knowledge Base

Store structured work information that remains useful long after the original work has been completed.

---

### Enable Future Career Intelligence

Lay the foundation for future capabilities including:

* accomplishment summaries
* resume generation
* performance review preparation
* interview preparation

These capabilities are intentionally outside the scope of the MVP.

---

# 5. Product Principles

The following principles govern the design of WorkGraph AI.

---

## Principle 1 — Minimise Friction

Logging work should require as little effort as possible.

The ideal interaction should feel indistinguishable from sending a message to a colleague.

Any feature that increases friction without proportional value should be reconsidered.

---

## Principle 2 — AI First

Users communicate in natural language.

The AI is responsible for:

* extracting entities
* organising information
* detecting relationships
* suggesting structure

The product should avoid exposing unnecessary complexity to the user.

---

## Principle 3 — Tasks, Not Tickets

WorkGraph AI is designed around ongoing workstreams rather than individual tickets.

Tasks represent evolving bodies of work that accumulate progress over days or weeks.

Daily updates contribute to task histories rather than existing as isolated events.

---

## Principle 4 — Platform Agnostic

The product should not depend on any specific workplace software.

It should support a wide range of communication tools, documentation platforms and analytics environments without requiring changes to the underlying product philosophy.

---

## Principle 5 — Career-Oriented

The purpose of documenting work is not merely archival.

The system should ultimately help users communicate their professional achievements more effectively throughout their careers.

---

## Principle 6 — Trust Before Automation

Artificial intelligence should reduce effort without reducing confidence.

The AI should recommend, infer and organise information, but users remain the final authority over their professional records.

Confidence-based confirmation should always take precedence over blind automation.

---

## Principle 7 — Continuous Learning

The system should improve through interaction.

User confirmations, corrections and edits should gradually personalise the AI's understanding of projects, terminology, stakeholders and work patterns while maintaining transparency and user control.

The objective is not merely to automate work logging, but to build an assistant that increasingly understands how its user works.

# 6. User Personas

WorkGraph AI is designed primarily for individual knowledge workers whose daily work consists of multiple concurrent initiatives, stakeholder communication, analysis, documentation and decision making.

The MVP focuses on a single-user experience. Multi-user collaboration is considered future work.

---

## Primary Persona — Data Analyst

### Profile

A Data Analyst works across multiple business initiatives simultaneously, often supporting different stakeholders while balancing ad hoc requests, recurring reporting and longer-term projects.

Typical responsibilities include:

* Writing SQL
* Building dashboards
* Performing exploratory analysis
* Investigating data issues
* Meeting with stakeholders
* Presenting insights
* Maintaining reporting pipelines

### Current Challenges

* Frequently interrupted by ad hoc requests.
* Works on many projects in parallel.
* Forgets to document completed work.
* Struggles to recall accomplishments months later.
* Finds spreadsheets tedious to maintain.

### Goals

* Capture work with minimal effort.
* Remember what was accomplished.
* Track project progress.
* Retrieve historical work quickly.
* Prepare performance reviews with confidence.

---

## Secondary Persona — Analytics Engineer

### Profile

An Analytics Engineer builds data models, dashboards and reporting infrastructure while collaborating closely with analysts and engineering teams.

Typical work includes:

* ETL development
* Data modelling
* Pipeline optimisation
* Dashboard development
* Data quality improvements
* Documentation

### Current Challenges

* Technical work evolves over several weeks.
* Important implementation decisions are forgotten.
* Difficult to reconstruct project timelines.

### Goals

* Maintain engineering history.
* Track implementation milestones.
* Preserve technical context.
* Build searchable project records.

---

## Secondary Persona — Product Manager

### Profile

Product Managers coordinate multiple initiatives across engineering, analytics and business teams.

Typical work includes:

* Stakeholder meetings
* Requirement gathering
* Product planning
* Roadmap discussions
* Cross-functional coordination

### Goals

* Maintain meeting history.
* Track product initiatives.
* Remember important decisions.
* Build project timelines.

---

## Future Personas

Although not included within the MVP, future versions may support:

* Software Engineers
* Machine Learning Engineers
* Consultants
* Researchers
* Designers
* Team Leads
* Managers

The underlying product philosophy remains unchanged regardless of profession.

---

# 7. User Journey

## Current Workflow

The current experience for many professionals resembles the following:

```text
Receive request

↓

Investigate

↓

Analyse

↓

Meeting

↓

Build solution

↓

Deliver

↓

Forget details
```

Documentation is often postponed until much later.

---

## Desired Workflow

WorkGraph AI introduces documentation directly into the user's existing workflow.

```text
Receive request

↓

Do work

↓

Send Telegram message

↓

AI structures information

↓

Confirm

↓

Continue working
```

The user spends only a few seconds documenting their work while the AI performs the administrative effort.

---

## End-to-End Journey

### Step 1 — Complete Work

The user finishes a task, investigation or meeting.

Example

> Investigated payment reconciliation issue today.

---

### Step 2 — Send Telegram Message

The user sends a natural language message.

Example

> Found duplicate joins causing incorrect totals. Finance confirmed the fix. QA tomorrow.

No predefined format is required.

---

### Step 3 — AI Processing

The system automatically:

* extracts entities
* identifies stakeholders
* detects status
* identifies next steps
* searches for existing tasks
* determines confidence
* prepares structured output

---

### Step 4 — User Confirmation

Depending on confidence:

High confidence

```text
Saved under:

Settlement Reconciliation

✓ Status updated

✓ Timeline updated
```

Medium confidence

```text
I think this belongs to:

Settlement Reconciliation

Is that correct?

[Yes]

[Choose Another]

[Create New]
```

Low confidence

```text
I couldn't confidently match this update.

Would you like to create a new task?
```

---

### Step 5 — Data Persistence

Once confirmed, the system updates:

* Tasks sheet
* Daily Logs sheet

The user never needs to manually edit Google Sheets.

---

### Step 6 — Future Retrieval

Weeks later, users may ask:

> What did I do for Finance this month?

or

> Show everything related to payment reconciliation.

The AI retrieves relevant work history.

---

# 8. Core User Experience

## UX Philosophy

Every interaction should satisfy three goals:

### Fast

Logging should take less than thirty seconds.

---

### Natural

Users communicate naturally rather than filling forms.

---

### Trustworthy

Users understand what the AI is doing and retain full control over important decisions.

---

## Design Principles

### Conversation First

The primary interface is conversation.

Users should never feel they are interacting with a database.

---

### AI Does the Heavy Lifting

The AI is responsible for:

* classification
* organisation
* matching
* summarisation
* enrichment

The user is responsible only for describing work.

---

### Progressive Disclosure

Simple tasks should remain simple.

Advanced functionality should appear only when needed.

---

### Minimal Confirmation

Users should not repeatedly answer unnecessary questions.

The system should learn from confirmations to reduce future friction.

---

# 9. Functional Requirements

## FR1 — Daily Logging

### Objective

Allow users to record work using free-form natural language.

---

### Behaviour

Users send one or more messages describing work completed during the day.

Examples

> Built SQL for dashboard refresh.

---

> Finance approved the reconciliation dashboard.

---

> Meeting with Product. Need another version tomorrow.

The system should accept conversational language without requiring predefined templates.

---

### Acceptance Criteria

* Messages processed within five seconds.
* No structured input required.
* Multiple sentences supported.
* Multiple topics supported.

---

## FR2 — AI Information Extraction

### Objective

Automatically transform natural language into structured information.

---

### Extracted Fields

The AI should identify:

* Date
* Task
* Stakeholder
* Status
* Resources
* Next Steps
* Tags
* Summary

Future versions may extract additional metadata.

---

### Acceptance Criteria

The AI correctly extracts key entities while preserving the original message.

---

## FR3 — Task Matching

### Objective

Associate each Daily Log with an existing Task whenever appropriate.

---

### Behaviour

The AI searches existing Tasks using semantic similarity rather than keyword matching.

Possible outcomes:

Existing Task

↓

Update timeline

Existing Task (uncertain)

↓

Ask for confirmation

No suitable Task

↓

Suggest new Task

---

### Acceptance Criteria

Users rarely need to manually search for tasks.

---

## FR4 — Task Creation

### Objective

Allow new workstreams to be created automatically.

---

### Behaviour

When no suitable task exists, the AI proposes creating a new task.

Example

Task

```
Customer Churn Dashboard
```

The user confirms before creation.

---

### Acceptance Criteria

Duplicate tasks should be minimised.

---

## FR5 — Task Timeline

### Objective

Maintain a chronological history for every task.

Example

```
22 Jul

Stakeholder requested dashboard.

↓

24 Jul

SQL completed.

↓

26 Jul

Dashboard published.

↓

28 Jul

Requested additional filters.
```

Users should not manually edit timelines.

---

## FR6 — Status Management

### Objective

Automatically infer task status.

Possible statuses include:

* Not Started
* In Progress
* Waiting for Feedback
* Waiting for QA
* Blocked
* Completed

Users may override AI suggestions.

---

## FR7 — Resource Management

### Objective

Track resources associated with work.

Resources may include:

* SQL queries
* Dashboards
* Documents
* Communication threads
* Repositories
* URLs

The AI should recognise these resources from user messages whenever possible.

---

## FR8 — Search

### Objective

Retrieve historical work using natural language.

Example queries

> Show work related to Finance.

---

> What dashboards did I build in July?

---

> Which projects are still waiting for QA?

The AI should return relevant Tasks and Daily Logs.

---

## FR9 — Editing

### Objective

Allow users to correct AI output.

Supported actions include:

* edit task
* edit stakeholder
* edit status
* edit tags
* edit next steps
* delete log
* undo last action

Corrections should contribute to future learning.

---

## FR10 — Daily Summary

### Objective

Allow users to review work logged during the current day.

Example

```
Today's Work

• Dashboard migration

• Payment investigation

• Stakeholder meeting

3 updates logged
```

This provides quick verification before the day ends.

---

## FR11 — Weekly Summary

### Objective

Generate a concise overview of work completed during the week.

Example outputs include:

* Tasks progressed
* Tasks completed
* Stakeholders involved
* Major accomplishments
* Pending next steps

This feature supports personal reflection without requiring manual reporting.

---

## FR12 — Reminder Notifications

### Objective

Encourage consistent usage without becoming intrusive.

The system should optionally send a reminder near the end of the workday if no work has been logged.

Example

> You haven't logged any work today.

> Anything you'd like me to remember?

Reminders should be configurable and easily disabled.

---

# 10. Telegram User Experience

## Primary Interface

Telegram serves as the primary interaction channel.

The interface should feel conversational rather than transactional.

---

## Example Interaction — New Task

**User**

> Built the first version of the Customer Churn Dashboard today.

**Bot**

```
I found a new piece of work.

Task:
Customer Churn Dashboard

Status:
In Progress

Stakeholder:
Marketing

Would you like to save it?

[Save]

[Edit]

[Cancel]
```

---

## Example Interaction — Existing Task

**User**

> Added requested filters after Finance feedback.

**Bot**

```
I matched this to:

Settlement Reconciliation

Changes

✓ Timeline updated

✓ Status remains In Progress

✓ Added today's update

Saved successfully.
```

---

## Example Interaction — Low Confidence

**User**

> Finished the dashboard.

**Bot**

```
I found multiple possible matches.

• Sales Dashboard (82%)

• Marketing Dashboard (76%)

• Campaign Dashboard (73%)

Which one should I use?
```

---

## Example Interaction — Search

**User**

> What did I work on last week?

**Bot**

```
Last Week

Tasks

• Settlement Reconciliation

• Campaign Dashboard

• Data Quality Investigation

Highlights

• Completed dashboard deployment

• Fixed duplicate joins

• QA completed

5 updates logged
```

---

## UX Requirements

The Telegram experience should prioritise:

* minimal typing
* concise responses
* actionable confirmations
* natural conversation
* low cognitive load

Every interaction should reinforce the feeling that the user is talking to an intelligent teammate rather than operating a database.

The interface should favour clarity over verbosity and should never expose unnecessary implementation details such as embeddings, similarity scores or database structures unless explicitly requested.

# 11. Google Sheets Data Model

## Overview

The MVP uses Google Sheets as the primary persistent storage layer.

Google Sheets was selected because it:

* requires minimal setup
* is free for individual users
* provides immediate visibility into stored data
* allows manual editing when required
* integrates easily with Python and Google APIs

The sheet acts as the **source of truth** for user-facing data, while the backend is responsible for all AI reasoning and business logic.

Future versions may migrate to PostgreSQL while preserving compatibility with the existing schema.

---

## Workbook Structure

The workbook contains two primary worksheets.

```text
WorkGraph AI

├── Tasks
└── Daily Logs
```

Additional worksheets may be introduced in future versions for configuration, analytics or learned knowledge.

---

# 11.1 Tasks Sheet

## Purpose

The Tasks sheet stores the current state of every ongoing or completed workstream.

Each row represents a single Task.

Tasks are intended to be long-lived entities that evolve over multiple days or weeks.

---

## Schema

| Column        | Description                  |
| ------------- | ---------------------------- |
| Task ID       | Unique identifier            |
| Task Name     | Human-readable task title    |
| Stakeholder   | Primary stakeholder          |
| Status        | Current task status          |
| Tags          | AI-generated tags            |
| Resources     | Related URLs or references   |
| Date Created  | First appearance             |
| Last Updated  | Most recent activity         |
| Total Updates | Number of linked Daily Logs  |
| Summary       | AI-generated rolling summary |

---

## Example

| Task ID | Task Name                 | Stakeholder | Status      |
| ------- | ------------------------- | ----------- | ----------- |
| T001    | Settlement Reconciliation | Finance     | Waiting QA  |
| T002    | AUM Dashboard             | Product     | In Progress |

---

## Task Summary

Each Task maintains a continuously updated summary.

Example

```text
Settlement Reconciliation

Investigating incorrect settlement totals caused by duplicate joins.

Finance has validated the fix.

Awaiting QA before deployment.
```

The summary should evolve automatically as new Daily Logs are added.

---

## Rolling Summary Behaviour

The AI should continuously refine the summary rather than simply appending new text.

Poor example

```text
Worked on SQL.

Worked on SQL.

Worked on SQL.
```

Preferred

```text
Built SQL solution for settlement reconciliation.

Finance approved the solution.

Deployment currently awaiting QA.
```

---

# 11.2 Daily Logs Sheet

## Purpose

The Daily Logs sheet stores every individual work update submitted by the user.

Unlike Tasks, Daily Logs are immutable historical records.

Each Daily Log belongs to exactly one Task.

---

## Schema

| Column           | Description                 |
| ---------------- | --------------------------- |
| Log ID           | Unique identifier           |
| Date             | Work date                   |
| Task ID          | Linked Task                 |
| Original Message | User's raw Telegram message |
| Stakeholder      | Extracted stakeholder       |
| Status           | AI-detected status          |
| Next Steps       | AI-detected next action     |
| Resources        | Related links               |
| Tags             | AI-generated tags           |
| Impact           | Estimated impact level      |
| Timestamp        | Submission timestamp        |

---

## Example

| Date   | Task                      | Status     |
| ------ | ------------------------- | ---------- |
| 26 Jul | Settlement Reconciliation | Waiting QA |

Original Message

> Finance approved the SQL fix. QA tomorrow.

---

## Immutable Records

Daily Logs should never be overwritten.

Corrections should modify extracted fields while preserving:

* original message
* submission timestamp
* historical context

This ensures future AI models can reprocess historical data if necessary.

---

# 11.3 Relationship Between Sheets

```text
Task

↓

Many Daily Logs

↓

Chronological Timeline
```

Example

```text
Settlement Reconciliation

↓

22 Jul

Stakeholder raised issue.

↓

24 Jul

Duplicate joins identified.

↓

26 Jul

Finance approved solution.

↓

28 Jul

Waiting QA.
```

The Tasks sheet stores the latest state.

The Daily Logs sheet stores the complete history.

---

# 12. AI Behaviour

## Overview

Artificial Intelligence is responsible for transforming unstructured conversation into structured professional knowledge.

The AI should minimise manual effort while maintaining transparency and user trust.

It is not responsible for making irreversible decisions.

---

## AI Responsibilities

The AI performs the following functions:

* Information extraction
* Task matching
* Task creation suggestions
* Status detection
* Stakeholder detection
* Resource recognition
* Tag generation
* Timeline updates
* Summary generation
* Impact estimation

Future responsibilities are described in the Future Work section.

---

## Processing Pipeline

```text
Telegram Message

↓

Pre-processing

↓

Information Extraction

↓

Task Matching

↓

Confidence Evaluation

↓

Decision Engine

↓

User Confirmation (if required)

↓

Google Sheets Update
```

Each stage is independent to allow future improvements without redesigning the entire system.

---

# Information Extraction

The AI converts free-form language into structured fields.

Example

User

> Product approved the dashboard today. Waiting for rollout next week.

Extracted

```text
Task

Dashboard Migration

Stakeholder

Product

Status

Waiting Deployment

Next Step

Rollout next week
```

Extraction should prioritise completeness while avoiding unsupported assumptions.

---

# Task Matching

The AI attempts to associate every Daily Log with an existing Task.

Matching should use semantic similarity rather than keyword equality.

The AI should consider:

* task title
* historical updates
* stakeholder
* resources
* recurring terminology
* learned abbreviations

Task matching should always occur before proposing a new Task.

---

# Status Detection

The AI should infer Task status based on message content.

Examples

| User Message                     | Suggested Status     |
| -------------------------------- | -------------------- |
| Investigating issue              | In Progress          |
| Waiting for stakeholder feedback | Waiting Feedback     |
| QA tomorrow                      | Waiting QA           |
| Ready for deployment             | Ready for Deployment |
| Released today                   | Completed            |

Users may modify incorrect suggestions.

---

# Resource Detection

Resources provide additional context.

Possible resources include:

* SQL queries
* dashboards
* documents
* repositories
* communication threads
* URLs

The AI should recognise resource types where possible.

Future integrations may enrich these resources with metadata.

---

# Tag Generation

Tags improve discoverability.

Example

```text
SQL

Dashboard

Experiment

Meeting

Bug

Automation
```

Tags should be generated automatically while remaining editable.

---

# Summary Generation

The AI should maintain:

* task summaries
* weekly summaries
* search summaries

Summaries should focus on outcomes rather than chronological repetition.

---

# Impact Detection

The AI estimates the significance of each Daily Log.

Possible labels include:

* Informational
* Low
* Medium
* High
* Critical

Impact estimation should consider:

* business outcome
* measurable improvements
* automation
* stakeholder influence
* deployment
* technical complexity

Impact remains advisory rather than authoritative.

---

# 13. Human-in-the-Loop Design

## Philosophy

The AI is an assistant.

The user remains the source of truth.

Important decisions should require appropriate user confirmation.

---

## Confidence-Based Automation

Every inference receives a confidence score.

The confidence score determines system behaviour.

| Confidence | Behaviour                                          |
| ---------- | -------------------------------------------------- |
| ≥95%       | Automatically apply changes and notify the user.   |
| 70–94%     | Ask for confirmation before saving.                |
| <70%       | Request clarification or suggest multiple options. |

---

## Example

User

> Updated dashboard after Finance feedback.

Bot

```text
I think this belongs to:

Settlement Reconciliation

Confidence

88%

Would you like to save it?

[Yes]

[Choose Another]

[Create New]
```

---

# Explainability

Whenever practical, the AI should explain why a recommendation was made.

Example

```text
Matched because:

• Similar wording

• Same stakeholder

• Similar historical updates

Confidence

92%
```

Explainability increases user trust while helping users identify incorrect assumptions.

---

# Original Message Preservation

Every Daily Log stores:

* original user message
* extracted fields
* confirmed fields

This enables:

* auditing
* future AI improvements
* correction recovery

The original message should never be modified.

---

# Reversible Actions

Users should be able to:

* undo last save
* edit extracted information
* restore previous task status
* remove accidental logs

The system should prioritise recoverability over aggressive automation.

---

# User Authority

The AI may suggest.

Only the user confirms.

Examples requiring confirmation include:

* creating new Tasks
* merging Tasks
* changing stakeholders
* changing status
* deleting information

---

# 14. Personalised Learning System

## Vision

WorkGraph AI should become increasingly personalised through continued interaction.

Rather than relying solely on generic language models, the application should learn how its user works.

The objective is to reduce repetitive confirmations while preserving accuracy.

---

## Learning Philosophy

The system learns only from confirmed user behaviour.

Examples include:

* accepted task matches
* corrected task matches
* accepted stakeholders
* edited statuses
* accepted tags
* manually created Tasks

Cancelled or uncertain interactions should not influence learning.

---

## User Knowledge Base

The backend maintains an internal knowledge base describing the user's work environment.

Possible learned information includes:

### Projects

```text
Settlement Reconciliation

AUM Dashboard

Fraud Monitoring
```

---

### Stakeholders

```text
Finance

Product

Risk

Marketing
```

---

### Abbreviations

```text
AUM

↓

AUM Dashboard

Prod

↓

Product
```

---

### Frequently Used Resources

Examples

* DataSuite SQL
* DataSuite Dashboard
* SeaTalk
* Google Sheets

These associations improve future extraction accuracy.

---

### Preferred Vocabulary

The AI should gradually learn preferred terminology.

Example

If the user consistently writes

> Investigated

instead of

> Debugged

future summaries should adopt the same writing style where appropriate.

---

## Continuous Learning Loop

```text
User Message

↓

AI Suggestion

↓

User Confirmation

↓

Learning Engine

↓

Knowledge Base

↓

Improved Future Suggestions
```

The objective is gradual improvement rather than immediate perfection.

---

## Adaptive Confidence

As the AI becomes more familiar with the user's work patterns, confidence scores should improve naturally.

Example

Month One

```text
Worked on AUM.

Confidence

61%
```

Month Three

```text
Worked on AUM.

Confidence

98%
```

This improvement comes from personalised learning rather than changes to the underlying language model.

---

## Privacy

Personal learning remains private to the individual user.

Users should be able to:

* inspect learned information
* edit learned information
* reset learned information
* export learned information

The learning system should never influence predictions for other users.

---

# 15. AI Trust & Explainability

## Trust Before Automation

Trust is considered more important than automation.

The AI should favour asking an additional question over making an incorrect assumption that permanently alters professional records.

---

## Transparency

The system should make its actions visible.

Users should understand:

* what was extracted
* what will be updated
* why a decision was made
* what confidence level was assigned

No significant changes should occur silently.

---

## Reliability

The AI should behave consistently.

Identical inputs under similar contexts should produce similar recommendations.

Unexpected behaviour should be minimised through deterministic prompts and confidence thresholds.

---

## Failure Handling

When uncertain, the AI should fail safely.

Examples include:

* asking for clarification
* presenting multiple task candidates
* preserving original messages
* avoiding unsupported assumptions

The system should never fabricate professional records.

---

## Success Metrics

The effectiveness of the AI should be measured through product outcomes rather than model benchmarks.

Primary indicators include:

* Task matching accuracy
* User confirmation rate
* Manual correction rate
* Daily logging consistency
* Time required to log work
* User trust and satisfaction

These metrics guide future iterations while ensuring the product remains focused on solving the user's problem rather than maximising automation for its own sake.

# 16. Non-Functional Requirements

## Overview

While functional requirements define **what** WorkGraph AI should do, non-functional requirements define **how** the system should behave.

The MVP should prioritise reliability, simplicity and maintainability over scale.

---

## 16.1 Performance

### Response Time

The system should respond quickly enough to avoid interrupting the user's workflow.

| Action                   | Target      |
| ------------------------ | ----------- |
| Telegram acknowledgement | < 2 seconds |
| AI extraction            | < 5 seconds |
| Save to Google Sheets    | < 3 seconds |
| Search request           | < 5 seconds |

Long-running operations should notify the user that processing is in progress.

---

### Availability

As WorkGraph AI functions as a personal productivity tool, high availability is desirable.

Target uptime:

* 99% for MVP
* 99.9% after production deployment

---

## 16.2 Reliability

The system should avoid data loss under all reasonable circumstances.

Requirements:

* Original user messages must never be discarded.
* Every successful submission must be persisted.
* Duplicate submissions should be detected where possible.
* Failed updates should be retried automatically.
* Partial writes should be avoided.

---

## 16.3 Maintainability

The codebase should be modular and easily extensible.

Key principles:

* Separation of concerns
* Service-oriented architecture
* Reusable AI components
* Clear interfaces
* Comprehensive documentation

Future integrations should require minimal modification to existing components.

---

## 16.4 Scalability

Although the MVP supports a single user, the architecture should not prevent future expansion.

Future scaling targets include:

* Multiple users
* Multiple workspaces
* Team collaboration
* Enterprise deployments
* Database migration
* Cloud-native deployment

Scalability should influence architecture but not unnecessarily complicate the MVP.

---

## 16.5 Security

The MVP stores professional work information and should therefore follow good security practices.

Requirements:

* HTTPS for all external communication
* Secure storage of API keys
* Environment variables for secrets
* Principle of least privilege
* Authentication for administrative endpoints
* Secure Google OAuth credentials

Secrets must never be committed to source control.

---

## 16.6 Privacy

User work history is personal and potentially confidential.

The system should:

* collect only required information
* avoid unnecessary data retention
* allow data export
* allow permanent deletion
* avoid sharing user information
* avoid using personal data for unrelated purposes

Personalised AI learning should remain isolated to the individual user.

---

## 16.7 Observability

The system should provide sufficient logging for debugging while avoiding sensitive content where unnecessary.

Recommended logging:

* Incoming requests
* AI processing duration
* Google Sheets updates
* Errors
* Retry attempts
* Confidence scores
* API usage

Sensitive message content should not be unnecessarily exposed in logs.

---

## 16.8 Cost Efficiency

The product should remain affordable for individual users.

Design considerations:

* minimise unnecessary LLM calls
* reuse previous context where appropriate
* cache embeddings
* batch operations where possible
* avoid repeated summarisation

Cost should scale approximately with usage rather than idle time.

---

# 17. Technical Constraints & Assumptions

## MVP Constraints

The first release intentionally limits technical complexity.

### Storage

Primary storage:

* Google Sheets

AI metadata may later migrate to SQLite or PostgreSQL.

---

### Interface

Primary interface:

* Telegram

No web interface is included in the MVP.

---

### AI

The application assumes access to a commercial Large Language Model via API.

The implementation should remain provider-agnostic to allow future migration between models.

---

### Deployment

The MVP should support deployment on low-cost cloud platforms.

Example options include:

* Railway
* Render
* Fly.io
* Google Cloud Run

---

### Authentication

Single-user authentication is assumed for the MVP.

Enterprise authentication is outside current scope.

---

## Assumptions

The PRD assumes:

* the user already uses Telegram regularly
* internet connectivity is available
* Google Sheets API remains available
* LLM API latency is acceptable
* users are willing to review AI suggestions

---

# 18. Future Work

The following capabilities are intentionally excluded from the MVP to maintain focus on solving the core problem of effortless work logging.

These ideas represent the long-term vision of WorkGraph AI.

---

# 18.1 AI Career Intelligence

Once sufficient work history has been accumulated, the platform can transform historical records into valuable career assets.

Potential capabilities include:

* Resume bullet generation
* STAR interview story generation
* Performance review drafting
* Promotion evidence generation
* Quarterly accomplishment reports
* Annual achievement summaries
* Leadership contribution summaries
* Technical portfolio generation

Example queries

> Generate my accomplishments from Q3.

> Write resume bullets based on my dashboard projects.

> Prepare STAR stories for behavioural interviews.

---

# 18.2 Multi-modal Logging

The MVP focuses on text-based interactions.

Future versions may support:

## Voice Logging

Users record a short voice note.

Speech is transcribed before entering the existing AI pipeline.

Example

```text
Voice Note

↓

Speech-to-Text

↓

LLM Extraction

↓

WorkGraph AI
```

---

## Screenshot Understanding

The AI analyses screenshots of:

* dashboards
* SQL editors
* documentation
* reports
* spreadsheets

Extracted information supplements the user's written update.

---

## OCR

Images containing text should be automatically processed.

Potential examples include:

* meeting notes
* whiteboards
* presentation slides

---

# 18.3 Knowledge Graph

Future versions may evolve beyond spreadsheets into a knowledge graph.

Instead of storing isolated rows, WorkGraph AI will model relationships between entities.

Example

```text
Stakeholder

↓

Project

↓

Dashboard

↓

SQL Query

↓

Meeting

↓

Daily Log

↓

Business Outcome
```

Potential technologies include:

* Neo4j
* Graph databases
* GraphRAG
* Hybrid semantic search

This enables richer questions such as:

* Which stakeholder have I collaborated with most?
* Which SQL queries supported multiple dashboards?
* Which projects contributed to Finance initiatives?

---

# 18.4 Integrations

The MVP intentionally avoids deep integrations.

Future integrations may include:

Communication

* SeaTalk
* Slack
* Microsoft Teams

Development

* GitHub
* GitLab

Calendars

* Google Calendar
* Outlook Calendar

Documentation

* Notion
* Confluence
* Google Docs

Analytics

* Tableau
* Power BI
* Looker

Native integrations should complement rather than replace conversational logging.

---

# 18.5 Analytics Dashboard

A future web dashboard may provide richer visualisation.

Potential features include:

* Active tasks
* Workload trends
* Stakeholder distribution
* Project timelines
* Weekly activity
* Monthly summaries
* Accomplishment trends
* Impact analytics

The dashboard should complement Telegram rather than become the primary interface.

---

# 18.6 Enterprise Features

Potential enterprise capabilities include:

* Multi-user workspaces
* Shared project timelines
* Manager dashboards
* Team analytics
* Role-based access control
* Audit trails
* Organisation-wide search
* SSO authentication

These features are intentionally excluded from the MVP.

---

# 18.7 AI Career Copilot

The long-term vision extends beyond work logging.

The AI becomes an intelligent career assistant capable of answering questions such as:

> What have I achieved this year?

> Which stakeholder have I delivered the most value to?

> Which projects demonstrate my machine learning experience?

> Generate evidence for my promotion discussion.

This represents the culmination of the platform's evolution rather than an immediate product goal.

---

# 19. Product Roadmap

The roadmap outlines the planned evolution of WorkGraph AI while maintaining a clear distinction between the MVP and future enhancements.

---

## Phase 1 — MVP

**Objective**

Create the fastest and easiest way to capture work history.

Core features:

* Telegram bot
* Google Sheets integration
* Daily logging
* AI extraction
* Task creation
* Task matching
* Timeline updates
* Status detection
* Resource detection
* Search
* Daily reminders
* Weekly summaries
* Human confirmation workflow

Success criteria:

* Logging takes less than 30 seconds.
* Users consistently log work.
* AI suggestions require minimal correction.

---

## Phase 2 — Intelligent Assistant

**Objective**

Improve contextual understanding.

New capabilities:

* Semantic task matching
* Duplicate detection
* Context-aware suggestions
* Enhanced summaries
* Confidence scoring improvements
* Smarter search
* Better resource recognition

---

## Phase 3 — Personalised Learning

**Objective**

Adapt to the user's working style.

Capabilities:

* Learn abbreviations
* Learn stakeholder aliases
* Learn preferred terminology
* Adaptive confidence thresholds
* User-editable knowledge base
* Personal vocabulary

Outcome:

The AI requires progressively fewer confirmations.

---

## Phase 4 — Career Intelligence

**Objective**

Transform work history into career assets.

Capabilities:

* Resume generation
* Performance review drafting
* STAR interview generation
* Achievement ranking
* Quarterly reports
* Promotion evidence

The platform begins functioning as a career assistant.

---

## Phase 5 — Knowledge Graph

**Objective**

Represent professional work as interconnected knowledge rather than isolated records.

Capabilities:

* Entity relationships
* Graph search
* Relationship visualisation
* Cross-project discovery
* GraphRAG
* Advanced semantic reasoning

This phase unlocks complex professional queries impossible with traditional spreadsheets.

---

## Phase 6 — AI Career Copilot

**Objective**

Provide proactive career guidance.

Potential capabilities:

* Identify professional strengths
* Highlight skill gaps
* Suggest portfolio improvements
* Recommend learning opportunities
* Prepare interview stories
* Assist with career planning

The AI evolves from a passive recorder into an active professional advisor.

---

# 20. Risks & Mitigation

| Risk                      | Impact    | Mitigation                                    |
| ------------------------- | --------- | --------------------------------------------- |
| Incorrect AI extraction   | Medium    | Human confirmation workflow                   |
| Duplicate tasks           | Medium    | Semantic similarity matching                  |
| User loses trust          | High      | Confidence scoring and explainability         |
| API outages               | Medium    | Retry logic and graceful failure              |
| Rising AI costs           | Medium    | Caching, batching and efficient prompting     |
| Google Sheets limitations | Low (MVP) | Future migration path to relational databases |

---

# 21. Success Metrics

The MVP will be evaluated using measurable product outcomes rather than AI benchmark scores.

## Adoption

* Daily logging frequency
* Weekly active usage
* Percentage of workdays logged

---

## Efficiency

* Average time to log work
* Number of user interactions per log
* Confirmation rate

---

## AI Quality

* Task matching accuracy
* Status prediction accuracy
* Stakeholder extraction accuracy
* Manual correction rate

---

## User Trust

Indicators include:

* Reduced manual edits over time
* Increased acceptance of AI suggestions
* Continued long-term usage

Trust is considered a primary success metric alongside accuracy.

---

# 22. Appendix

## Glossary

| Term             | Definition                                                                |
| ---------------- | ------------------------------------------------------------------------- |
| Task             | An ongoing workstream that spans multiple updates.                        |
| Daily Log        | A single work update submitted by the user.                               |
| Stakeholder      | A person or team requesting or affected by the work.                      |
| Resource         | Any supporting reference such as a dashboard, SQL query, document or URL. |
| Timeline         | Chronological sequence of Daily Logs belonging to a Task.                 |
| Confidence Score | The AI's estimated certainty for a prediction or recommendation.          |
| Knowledge Base   | Personalised information learned from confirmed user interactions.        |

---

## Out of Scope (MVP)

The following are intentionally excluded from the initial release:

* Team collaboration
* Enterprise administration
* Native mobile application
* Web dashboard
* Knowledge graph implementation
* Voice logging
* Screenshot understanding
* Calendar synchronisation
* Automatic integrations with workplace software
* Resume generation
* Performance review generation
* Promotion assistance
* AI career coaching

These capabilities remain part of the long-term vision but should not delay delivery of the MVP.

---

# Conclusion

WorkGraph AI is designed to remove the friction associated with documenting professional work by combining conversational interfaces, artificial intelligence and structured knowledge management.

The MVP deliberately focuses on a single, well-defined problem: **making work logging effortless**.

Every additional capability—from personalised learning to career intelligence and knowledge graphs—is built upon the foundation of accurate, trusted and low-friction work capture.

By prioritising simplicity, transparency and human oversight, WorkGraph AI aims to become more than a productivity tool. It aspires to be a trusted professional memory that grows alongside its user, preserving not only what they accomplished, but also the context, relationships and impact behind that work.
