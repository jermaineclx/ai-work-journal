"""Evaluation harness for the Extraction Agent (03_IMPLEMENTATION.md §26).

Runs the real LLM provider against `evaluation/sample_logs/*.txt` and
checks the output against the matching `evaluation/expected_outputs/*.json`
file. This is a manual/benchmark tool (requires a real API key) — not
part of the automated pytest suite, which must run without network
access or credentials.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from app.ai.extraction import ExtractionAgent
from app.ai.providers.factory import get_llm_provider

_EVAL_DIR = Path(__file__).resolve().parents[3] / "evaluation"


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    details: list[str]


def _check_contains(actual: str | None, expected_substring: str | None) -> tuple[bool, str]:
    if expected_substring is None:
        return True, "ok (no expectation)"
    if actual and expected_substring.lower() in actual.lower():
        return True, "ok"
    return False, f"expected to contain '{expected_substring}', got '{actual}'"


def _check_equals(actual: str | None, expected: str | None) -> tuple[bool, str]:
    if expected is None:
        return True, "ok (no expectation)"
    if actual == expected:
        return True, "ok"
    return False, f"expected '{expected}', got '{actual}'"


async def run_evaluation() -> list[EvalResult]:
    agent = ExtractionAgent(get_llm_provider())
    sample_dir = _EVAL_DIR / "sample_logs"
    expected_dir = _EVAL_DIR / "expected_outputs"

    results: list[EvalResult] = []
    for sample_path in sorted(sample_dir.glob("*.txt")):
        case_id = sample_path.stem
        expected_path = expected_dir / f"{case_id}.json"
        if not expected_path.exists():
            continue

        message = sample_path.read_text(encoding="utf-8").strip()
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        extraction, _version = await agent.run(message=message, known_stakeholders=[], known_tasks=[], known_aliases={})

        details: list[str] = []
        passed = True

        ok, detail = _check_contains(extraction.task_title, expected.get("task_title_contains"))
        details.append(f"task_title: {detail}")
        passed &= ok

        ok, detail = _check_equals(extraction.stakeholder, expected.get("stakeholder"))
        details.append(f"stakeholder: {detail}")
        passed &= ok

        ok, detail = _check_contains(extraction.status_hint, expected.get("status_hint_contains"))
        details.append(f"status_hint: {detail}")
        passed &= ok

        results.append(EvalResult(case_id=case_id, passed=passed, details=details))

    return results


def main() -> None:
    results = asyncio.run(run_evaluation())
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case_id}")
        for detail in r.details:
            print(f"    {detail}")
    print(f"\n{passed}/{total} cases passed")


if __name__ == "__main__":
    main()
