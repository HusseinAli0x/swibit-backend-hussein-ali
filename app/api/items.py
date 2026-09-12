from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.crud import item as item_crud
from app.crud import list as list_crud
from app.models.user import User
from app.schemas.common import Page, Pagination
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/lists/{list_id}/items", tags=["items"])


def _get_owned_list_or_404(db: Session, list_id: int, owner_id: int):
    obj = list_crud.get_owned(db, list_id, owner_id)
    if obj is None:
        raise NotFoundError("List not found.")
    return obj


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    list_id: int,
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemRead:
    # 404s instead of 403 when the list belongs to someone else - adding an
    # item to another user's list must be rejected without confirming the
    # list id even exists.
    _get_owned_list_or_404(db, list_id, current_user.id)
    obj = item_crud.create(db, list_id=list_id, data=data)
    return ItemRead.model_validate(obj)


@router.get("", response_model=Page[ItemRead])
def get_items(
    list_id: int,
    pagination: Pagination = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ItemRead]:
    _get_owned_list_or_404(db, list_id, current_user.id)
    rows, total = item_crud.list_for_list(
        db, list_id=list_id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[ItemRead](
        items=[ItemRead.model_validate(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def _get_owned_item_or_404(db: Session, item_id: int, list_id: int, owner_id: int):
    obj = item_crud.get_owned(db, item_id, list_id, owner_id)
    if obj is None:
        raise NotFoundError("Item not found.")
    return obj


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemRead:
    obj = _get_owned_item_or_404(db, item_id, list_id, current_user.id)
    return ItemRead.model_validate(obj)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    list_id: int,
    item_id: int,
    data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemRead:
    obj = _get_owned_item_or_404(db, item_id, list_id, current_user.id)
    obj = item_crud.update(db, obj, data)
    return ItemRead.model_validate(obj)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    obj = _get_owned_item_or_404(db, item_id, list_id, current_user.id)
    item_crud.delete(db, obj)
