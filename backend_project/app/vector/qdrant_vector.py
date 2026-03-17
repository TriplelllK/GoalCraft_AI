from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from typing import Any, Optional

import requests

from app.models.schemas import Document
from app.services.rules import chunk_text, overlap_ratio, tokenize
from app.vector.memory_vector import ChunkRecord


@dataclass
class SearchResult(ChunkRecord):
    vector_score: float = 0.0


class QdrantVectorStore:
    """Qdrant integration via REST API.

    Uses a deterministic lightweight hashing embedder so the service can be indexed
    without heavyweight ML dependencies. This keeps the backend runnable while still
    providing a real vector database integration. You can later swap `_embed` with
    BGE-M3 embeddings without changing the API surface.
    """

    def __init__(self, url: str, api_key: str, collection: str, vector_size: int = 256, timeout: float = 10.0) -> None:
        if not url:
            raise ValueError("QDRANT_URL is required for QdrantVectorStore")
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.collection = collection
        self.vector_size = vector_size
        self.timeout = timeout
        self._session = requests.Session()
        self._chunks_by_id: dict[str, SearchResult] = {}
        self.ensure_collection()

    @property
    def backend_name(self) -> str:
        return "qdrant"

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def ping(self) -> dict[str, Any]:
        response = self._session.get(f"{self.url}/collections", headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return {"backend": "qdrant", "ok": True, "collection": self.collection}

    def count(self) -> int:
        try:
            response = self._session.post(
                f"{self.url}/collections/{self.collection}/points/count",
                headers=self._headers,
                json={"exact": True},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return int(response.json().get("result", {}).get("count", 0))
        except Exception:
            return len(self._chunks_by_id)

    def ensure_collection(self, retries: int = 20, delay: float = 1.0) -> None:
        payload = {
            "vectors": {
                "size": self.vector_size,
                "distance": "Cosine",
            }
        }
        last_error: Optional[Exception] = None
        for _ in range(retries):
            try:
                response = self._session.put(
                    f"{self.url}/collections/{self.collection}",
                    headers=self._headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code in {200, 201}:
                    return
                response.raise_for_status()
            except Exception as exc:  # pragma: no cover - external service timing
                last_error = exc
                time.sleep(delay)
        raise RuntimeError(f"Failed to create/connect Qdrant collection {self.collection}: {last_error}")

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.vector_size
        tokens = tokenize(text)
        if not tokens:
            return vec
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "little") % self.vector_size
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[slot] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 8) for x in vec]

    def index_documents(self, documents: list[Document]) -> int:
        points: list[dict[str, Any]] = []
        local_chunks: dict[str, SearchResult] = {}
        for doc in documents:
            for idx, part in enumerate(chunk_text(doc.content), start=1):
                chunk_id = f"{doc.doc_id}::{idx}"
                payload = {
                    "chunk_id": chunk_id,
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "text": part,
                    "keywords": doc.keywords,
                    "owner_department_id": doc.owner_department_id,
                    "department_scope": doc.department_scope,
                }
                points.append({
                    "id": int(hashlib.md5(chunk_id.encode('utf-8')).hexdigest()[:12], 16),
                    "vector": self._embed(f"{doc.title} {part} {' '.join(doc.keywords)}"),
                    "payload": payload,
                })
                local_chunks[chunk_id] = SearchResult(**payload, vector_score=0.0)
        if not points:
            self._chunks_by_id = {}
            return 0
        response = self._session.put(
            f"{self.url}/collections/{self.collection}/points?wait=true",
            headers=self._headers,
            json={"points": points},
            timeout=max(self.timeout, 30.0),
        )
        response.raise_for_status()
        self._chunks_by_id = local_chunks
        return len(points)

    def search(self, query: str, department_id: Optional[str] = None, top_k: int = 5) -> list[SearchResult]:
        qdrant_filter: dict[str, Any] | None = None
        if department_id:
            qdrant_filter = {
                "should": [
                    {"key": "department_scope", "match": {"value": department_id}},
                    {"key": "owner_department_id", "match": {"value": department_id}},
                ]
            }
        response = self._session.post(
            f"{self.url}/collections/{self.collection}/points/search",
            headers=self._headers,
            json={
                "vector": self._embed(query),
                "limit": top_k * 3,
                "with_payload": True,
                **({"filter": qdrant_filter} if qdrant_filter else {}),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        hits = response.json().get("result", [])
        scored: list[tuple[float, SearchResult]] = []
        for hit in hits:
            payload = hit.get("payload", {})
            if department_id:
                scope = payload.get("department_scope") or []
                owner = payload.get("owner_department_id")
                if scope and department_id not in scope and owner != department_id:
                    continue
            lexical_bonus = overlap_ratio(query, f"{payload.get('text', '')} {' '.join(payload.get('keywords') or [])}")
            final_score = (float(hit.get("score", 0.0)) * 0.7) + (lexical_bonus * 0.3)
            record = SearchResult(
                chunk_id=payload.get("chunk_id", ""),
                doc_id=payload.get("doc_id", ""),
                title=payload.get("title", ""),
                doc_type=payload.get("doc_type", ""),
                text=payload.get("text", ""),
                keywords=list(payload.get("keywords") or []),
                owner_department_id=payload.get("owner_department_id"),
                department_scope=list(payload.get("department_scope") or []),
                vector_score=round(final_score, 4),
            )
            scored.append((final_score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
