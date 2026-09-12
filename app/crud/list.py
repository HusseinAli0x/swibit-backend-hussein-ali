from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.list import List as ListModel
from app.schemas.list import ListCreate, ListUpdate


def create(db: Session, owner_id: int, data: ListCreate) -> ListModel:
    obj = ListModel(owner_id=owner_id, title=data.title, description=data.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_owned(db: Session, list_id: int, owner_id: int) -> ListModel | None:
    """Fetch a list only if it belongs to `owner_id`; otherwise None (never leaks existence)."""
    stmt = select(ListModel).where(ListModel.id == list_id, ListModel.owner_id == owner_id)
    return db.execute(stmt).scalar_one_or_none()


def list_for_owner(
    db: Session, owner_id: int, limit: int, offset: int
) -> tuple[list[ListModel], int]:
    base = select(ListModel).where(ListModel.owner_id == owner_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    rows = db.execute(
        base.order_by(ListModel.id.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return list(rows), total


def update(db: Session, obj: ListModel, data: ListUpdate) -> ListModel:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: ListModel) -> None:
    db.delete(obj)
    db.commit()
