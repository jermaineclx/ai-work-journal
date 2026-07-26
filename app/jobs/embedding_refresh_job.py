"""Nightly embedding-refresh safety net (03_IMPLEMENTATION.md §22).

Task embeddings are already refreshed synchronously after every commit
(see LogService/TaskService), so this job mainly guards against drift
from any out-of-band edits (e.g. direct spreadsheet edits) and ensures
every Task has an embedding at all.
"""

from __future__ import annotations

from app.core.container import Container
from app.core.logging import get_logger

logger = get_logger(__name__)


async def refresh_all_embeddings(container: Container) -> None:
    tasks = await container.task_repo.get_all()
    await container.embedding_refresher.refresh_all(tasks)
    logger.info("embeddings_refreshed", extra={"count": len(tasks)})
