from typing import Generic, TypeVar, List, Optional, Dict, Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

M = TypeVar('M')
K = TypeVar('K')


class AbstractRepository(Generic[M, K]):
    def __init__(self, db: Session, model: type[M]):
        self.db = db
        self.model = model
        self._default_load_options = []

    def with_load(self, *options: Any) -> 'AbstractRepository':
        self._default_load_options.extend(options)
        return self

    def _apply_load_options(self, query):
        if self._default_load_options:
            query = query.options(*self._default_load_options)
        return query

    def get(self, id: K) -> Optional[M]:
        query = self.db.query(self.model)
        query = self._apply_load_options(query)
        return query.filter(self.model.id == id).first()

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            desc_order: bool = False
    ) -> List[M]:
        query = self.db.query(self.model)
        query = self._apply_load_options(query)

        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                if desc_order:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))

        return query.offset(skip).limit(limit).all()

    def create(self, data: Dict[str, Any]) -> M:
        db_obj = self.model(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: K, data: Dict[str, Any]) -> Optional[M]:
        db_obj = self.get(id)
        if db_obj:
            for key, value in data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: K) -> bool:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def filter(
            self,
            skip: int = 0,
            limit: int = 100,
            **filters: Any
    ) -> List[M]:
        query = self.db.query(self.model)
        query = self._apply_load_options(query)

        for attr, value in filters.items():
            if hasattr(self.model, attr):
                if isinstance(value, list):
                    query = query.filter(getattr(self.model, attr).in_(value))
                else:
                    query = query.filter(getattr(self.model, attr) == value)

        return query.offset(skip).limit(limit).all()

    def get_by_field(self, field_name: str, value: Any) -> Optional[M]:
        if hasattr(self.model, field_name):
            query = self.db.query(self.model)
            query = self._apply_load_options(query)
            return query.filter(getattr(self.model, field_name) == value).first()
        return None

    def exists(self, id: K) -> bool:
        return self.db.query(
            self.db.query(self.model).filter_by(id=id).exists()
        ).scalar()

    def count(self) -> int:
        return self.db.query(self.model).count()
