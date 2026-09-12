from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.list import List as ListModel
from app.schemas.item import ItemCreate, ItemUpdate


def create(db: Session, list_id: int, data: ItemCreate) -> Item:
    obj = Item(list_id=list_id, title=data.title, status=data.status, description=data.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_owned(db: Session, item_id: int, list_id: int, owner_id: int) -> Item | None:
    """Fetch an item only if it belongs to `list_id`, which in turn belongs to `owner_id`."""
    stmt = (
        select(Item)
        .join(ListModel, Item.list_id == ListModel.id)
        .where(Item.id == item_id, Item.list_id == list_id, ListModel.owner_id == owner_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_for_list(
    db: Session, list_id: int, limit: int, offset: int
) -> tuple[list[Item], int]:
    base = select(Item).where(Item.list_id == list_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    rows = db.execute(base.order_by(Item.id.desc()).limit(limit).offset(offset)).scalars().all()
    return list(rows), total


def update(db: Session, obj: Item, data: ItemUpdate) -> Item:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: Item) -> None:
    db.delete(obj)
    db.commit()
