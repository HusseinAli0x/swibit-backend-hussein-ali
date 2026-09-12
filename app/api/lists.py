from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.crud import list as list_crud
from app.models.user import User
from app.schemas.common import Page, Pagination
from app.schemas.list import ListCreate, ListRead, ListUpdate

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("", response_model=ListRead, status_code=status.HTTP_201_CREATED)
def create_list(
    data: ListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListRead:
    obj = list_crud.create(db, owner_id=current_user.id, data=data)
    return ListRead.model_validate(obj)


@router.get("", response_model=Page[ListRead])
def get_lists(
    pagination: Pagination = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ListRead]:
    rows, total = list_crud.list_for_owner(
        db, owner_id=current_user.id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[ListRead](
        items=[ListRead.model_validate(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def _get_owned_or_404(db: Session, list_id: int, owner_id: int):
    obj = list_crud.get_owned(db, list_id, owner_id)
    if obj is None:
        # Same error for "doesn't exist" and "belongs to someone else": never
        # reveal whether a resource id exists for a different owner.
        raise NotFoundError("List not found.")
    return obj


@router.get("/{list_id}", response_model=ListRead)
def get_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListRead:
    obj = _get_owned_or_404(db, list_id, current_user.id)
    return ListRead.model_validate(obj)


@router.patch("/{list_id}", response_model=ListRead)
def update_list(
    list_id: int,
    data: ListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListRead:
    obj = _get_owned_or_404(db, list_id, current_user.id)
    obj = list_crud.update(db, obj, data)
    return ListRead.model_validate(obj)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    obj = _get_owned_or_404(db, list_id, current_user.id)
    list_crud.delete(db, obj)
