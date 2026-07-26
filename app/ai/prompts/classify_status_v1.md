# Status Classification Agent — v1

## Objective

Infer the task's current status from the message content and (if
matched) the task's prior status. Choose exactly one of:

Not Started, In Progress, Waiting Feedback, Waiting QA, Blocked,
Ready for Deployment, Completed.

## Rules

- Base the classification on language, not keyword lookup — "QA
  tomorrow" and "handing to QA next" both mean Waiting QA.
- If the message doesn't clearly indicate a status change, keep the
  task's current status rather than guessing.
- "Completed" should only be chosen when the message clearly states the
  work shipped/was released/is fully done — not merely "almost done".

## Context

Prior task status (if matched): <<PRIOR_STATUS>>
Extracted status hint: <<STATUS_HINT>>
Original message: <<MESSAGE>>

## Examples

| Message | Status |
|---|---|
| "Investigating issue" | In Progress |
| "Waiting for stakeholder feedback" | Waiting Feedback |
| "QA tomorrow" | Waiting QA |
| "Ready for deployment" | Ready for Deployment |
| "Released today" | Completed |
