from __future__ import annotations

from app.core.config import settings
from app.services.engine import GoalEngine
from app.storage.memory import MemoryStore
from app.storage.postgres import PostgresStore
from app.vector.memory_vector import MemoryVectorStore
from app.vector.qdrant_vector import QdrantVectorStore


class AppContainer:
    def __init__(self) -> None:
        self.settings = settings
        self.store = self._build_store()
        self.vector_store = self._build_vector_store()
        self.engine = GoalEngine(self.store, self.vector_store)

    def _build_store(self):
        if self.settings.storage_backend == "postgres":
            return PostgresStore(
                database_url=self.settings.database_url,
                auto_init=self.settings.postgres_auto_init,
            )
        return MemoryStore()

    def _build_vector_store(self):
        if self.settings.vector_backend == "qdrant":
            return QdrantVectorStore(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                collection=self.settings.vector_collection,
                vector_size=self.settings.vector_size,
            )
        return MemoryVectorStore()


container = AppContainer()
