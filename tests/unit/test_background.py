"""Tests for the fire-and-forget background task helper."""

from __future__ import annotations

import pytest

from app.utils.background import fire_and_forget, wait_for_background_tasks


@pytest.mark.asyncio
async def test_fire_and_forget_runs_to_completion():
    ran = False

    async def do_work() -> None:
        nonlocal ran
        ran = True

    fire_and_forget(do_work(), name="test_task")
    await wait_for_background_tasks()

    assert ran is True


@pytest.mark.asyncio
async def test_fire_and_forget_does_not_raise_on_failure():
    """A failing background task must not propagate to the caller —
    only get logged. If this raises, fire_and_forget is broken."""

    async def failing_work() -> None:
        raise ValueError("boom")

    fire_and_forget(failing_work(), name="test_failing_task")
    await wait_for_background_tasks()  # must not raise
