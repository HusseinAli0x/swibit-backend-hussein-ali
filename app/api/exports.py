from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ConflictError, NotFoundError
from app.crud import export as export_crud
from app.crud import list as list_crud
from app.models.export_job import ExportStatus
from app.models.user import User
from app.schemas.common import Page, Pagination
from app.schemas.export import ExportJobRead
from app.workers.export import run_export_job

router = APIRouter(tags=["exports"])


@router.post(
    "/lists/{list_id}/exports",
    response_model=ExportJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_export(
    list_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportJobRead:
    source = list_crud.get_owned(db, list_id, current_user.id)
    if source is None:
        raise NotFoundError("List not found.")

    job = export_crud.create(db, owner_id=current_user.id, list_id=list_id)
    # Scheduled after the response is sent; the request never waits on it.
    background_tasks.add_task(run_export_job, job.id, current_user.id, list_id)
    return ExportJobRead.model_validate(job)


@router.get("/exports", response_model=Page[ExportJobRead])
def get_exports(
    pagination: Pagination = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ExportJobRead]:
    rows, total = export_crud.list_for_owner(
        db, owner_id=current_user.id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[ExportJobRead](
        items=[ExportJobRead.model_validate(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def _get_owned_job_or_404(db: Session, job_id: int, owner_id: int):
    job = export_crud.get_owned(db, job_id, owner_id)
    if job is None:
        raise NotFoundError("Export job not found.")
    return job


@router.get("/exports/{job_id}", response_model=ExportJobRead)
def get_export(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportJobRead:
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    return ExportJobRead.model_validate(job)


@router.get("/exports/{job_id}/download")
def download_export(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    if job.status != ExportStatus.COMPLETED or not job.file_path:
        raise ConflictError(
            f"Export job is '{job.status.value}'; only a completed job can be downloaded.",
            code="export_not_ready",
        )
    return FileResponse(job.file_path, media_type="application/json", filename=f"export_{job.id}.json")
