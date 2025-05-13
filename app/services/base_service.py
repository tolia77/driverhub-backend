from typing import Generic, TypeVar, List, Optional, Any, Type
from pydantic import BaseModel
from app.repositories.base_repository import BaseRepository

T = TypeVar('T', bound=BaseModel)
U = TypeVar('U', bound=BaseModel)
K = TypeVar('K')
M = TypeVar('M')
R = TypeVar('R', bound=BaseRepository)


class BaseService(Generic[T, U, K, M, R]):
    def __init__(self, repository: R, model: Type[M]):
        self.model = model
        self.repository = repository

    def get(self, id: K) -> Optional[M]:
        return self.repository.get(id)

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            desc_order: bool = False
    ) -> List[M]:
        return self.repository.get_all(
            skip=skip,
            limit=limit,
            order_by=order_by,
            desc_order=desc_order
        )

    def create(self, data: T) -> M:
        model = self._create_model_from_data(data)
        return self.repository.create(model)

    def update(self, id: K, data: U) -> Optional[M]:
        update_data = data.model_dump(exclude_unset=True)
        return self.repository.update(id, update_data)

    def delete(self, id: K) -> bool:
        return self.repository.delete(id)

    def filter(self, **filters: Any) -> List[M]:
        return self.repository.filter(**filters)

    def exists(self, id: K) -> bool:
        return self.repository.exists(id)

    def _create_model_from_data(self, data: T) -> M:
        data_dict = data.model_dump(exclude_unset=True)
        return self.model(**data_dict)