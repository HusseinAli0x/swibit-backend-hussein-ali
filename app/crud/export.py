from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.export_job import ExportJob, ExportStatus


def create(db: Session, owner_id: int, list_id: int) -> ExportJob:
    job = ExportJob(owner_id=owner_id, list_id=list_id, status=ExportStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_owned(db: Session, job_id: int, owner_id: int) -> ExportJob | None:
    stmt = select(ExportJob).where(ExportJob.id == job_id, ExportJob.owner_id == owner_id)
    return db.execute(stmt).scalar_one_or_none()


def list_for_owner(
    db: Session, owner_id: int, limit: int, offset: int
) -> tuple[list[ExportJob], int]:
    base = select(ExportJob).where(ExportJob.owner_id == owner_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    rows = db.execute(
        base.order_by(ExportJob.id.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return list(rows), total


def mark_completed(db: Session, job: ExportJob, file_path: str) -> None:
    job.status = ExportStatus.COMPLETED
    job.file_path = file_path
    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def mark_failed(db: Session, job: ExportJob, error_message: str) -> None:
    job.status = ExportStatus.FAILED
    job.error_message = error_message[:2000]
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
