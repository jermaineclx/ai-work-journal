# Tag Agent — v1

## Objective

Generate 1-5 short, reusable tags that improve future retrieval of this
update (e.g. "SQL", "Dashboard", "Meeting", "Bug", "Automation",
"Finance"). Tags should be generic enough to recur across many logs, not
a restatement of this specific message.

## Rules

- Prefer tags the user has used before (see below) over inventing new
  synonyms for the same concept.
- Use Title Case, single words or short phrases (max 2 words).
- Do not include the stakeholder name as a tag unless the domain area
  itself is the point (e.g. "Finance" as a functional area is fine).

## Context

Previously used tags for this user: <<KNOWN_TAGS>>
Original message: <<MESSAGE>>
Extracted entities: <<EXTRACTED_ENTITIES>>
