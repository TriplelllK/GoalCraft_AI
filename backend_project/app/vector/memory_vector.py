"""Lightweight in-memory vector store using deterministic hashing embeddings."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Optional

from app.models.schemas import Document
from app.services.rules import chunk_text, overlap_ratio, tokenize


@dataclass
class ChunkRecord:
    chunk_id: str = ""
    doc_id: str = ""
    title: str = ""
    doc_type: str = ""
    text: str = ""
    keywords: list[str] = field(default_factory=list)
    owner_department_id: Optional[str] = None
    department_scope: list[str] = field(default_factory=list)


class MemoryVectorStore:
    """Pure-Python vector store for demo / testing without external services."""

    VECTOR_SIZE = 256

    def __init__(self) -> None:
        self.chunks: list[ChunkRecord] = []
        self._vectors: list[list[float]] = []

    @property
    def backend_name(self) -> str:
        return "memory"

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.VECTOR_SIZE
        tokens = tokenize(text)
        if not tokens:
            return vec
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "little") % self.VECTOR_SIZE
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[slot] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 8) for x in vec]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
        norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (norm_a * norm_b)

    def index_documents(self, documents: list[Document]) -> int:
        self.chunks.clear()
        self._vectors.clear()
        for doc in documents:
            for idx, part in enumerate(chunk_text(doc.content), start=1):
                record = ChunkRecord(
                    chunk_id=f"{doc.doc_id}::{idx}",
                    doc_id=doc.doc_id,
                    title=doc.title,
                    doc_type=doc.doc_type,
                    text=part,
                    keywords=list(doc.keywords),
                    owner_department_id=doc.owner_department_id,
                    department_scope=list(doc.department_scope),
                )
                self.chunks.append(record)
                self._vectors.append(
                    self._embed(f"{doc.title} {part} {' '.join(doc.keywords)}")
                )
        return len(self.chunks)

    def search(self, query: str, department_id: str | None = None, top_k: int = 5) -> list[ChunkRecord]:
        if not self.chunks:
            return []
        query_vec = self._embed(query)
        scored: list[tuple[float, ChunkRecord]] = []
        for chunk, vec in zip(self.chunks, self._vectors):
            # Filter by department scope
            if department_id:
                if chunk.department_scope and department_id not in chunk.department_scope:
                    if chunk.owner_department_id != department_id:
                        continue
            cos = self._cosine(query_vec, vec)
            lexical = overlap_ratio(
                query,
                f"{chunk.text} {' '.join(chunk.keywords)}",
            )
            final = cos * 0.7 + lexical * 0.3
            scored.append((final, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
