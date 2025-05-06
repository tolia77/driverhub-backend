from abc import ABC
from typing import Generic, TypeVar, List, Optional, Any

from app.repositories.abstract_repository import AbstractRepository

T = TypeVar('T')
K = TypeVar('K')
M = TypeVar('M')
R = TypeVar('R', bound=AbstractRepository)


class AbstractService(Generic[T, K, M, R], ABC):
    def __init__(self, repository: R):
        self.repository = repository

    async def get(self, id: K) -> Optional[M]:
        return self.repository.get(id)

    async def get_all(
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

    async def create(self, data: T) -> M:
        return self.repository.create(data.dict())

    async def update(self, id: K, data: T) -> Optional[M]:
        return self.repository.update(id, data.dict(exclude_unset=True))

    async def delete(self, id: K) -> bool:
        return self.repository.delete(id)

    async def filter(self, **filters: Any) -> List[M]:
        return self.repository.filter(**filters)

    async def exists(self, id: K) -> bool:
        return self.repository.exists(id)
