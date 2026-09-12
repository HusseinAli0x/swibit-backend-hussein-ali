"""In-process background export worker.

Runs via FastAPI's `BackgroundTasks` after the HTTP response for the export
request has already been sent. It opens its own DB session because the
request-scoped session (from `get_db`) is closed by the time this runs.

Reliability trade-offs of this approach are documented in DESIGN.md.
"""
import json
import logging
import os
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import SessionLocal
from app.crud import export as export_crud
from app.crud import list as list_crud

logger = logging.getLogger(__name__)


def run_export_job(job_id: int, owner_id: int, list_id: int) -> None:
    db = SessionLocal()
    try:
        job = export_crud.get_owned(db, job_id, owner_id)
        if job is None:
            logger.error("export job %s vanished before it could run", job_id)
            return

        try:
            source = list_crud.get_owned(db, list_id, owner_id)
            if source is None:
                raise ValueError(f"list {list_id} no longer exists or is not owned by user")

            payload = {
                "list": {
                    "id": source.id,
                    "title": source.title,
                    "description": source.description,
                },
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "status": item.status.value,
                        "description": item.description,
                    }
                    for item in source.items
                ],
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

            os.makedirs(settings.export_dir, exist_ok=True)
            file_path = os.path.join(settings.export_dir, f"export_{job_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            export_crud.mark_completed(db, job, file_path)
        except Exception as exc:  # noqa: BLE001 - job failure must never propagate
            logger.exception("export job %s failed", job_id)
            export_crud.mark_failed(db, job, str(exc))
    finally:
        db.close()
