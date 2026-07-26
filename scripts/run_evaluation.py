#!/usr/bin/env python
"""Run the AI extraction evaluation benchmark against real API credentials.

Usage: python scripts/run_evaluation.py
Requires ANTHROPIC_API_KEY (and a valid .env) — this makes real LLM calls.
"""

from app.ai.evaluation.runner import main

if __name__ == "__main__":
    main()
