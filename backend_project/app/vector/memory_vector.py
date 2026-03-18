"""Enhanced in-memory vector store with n-gram embeddings, BM25 scoring and keyword boosting."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
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


@dataclass
class ScoredChunk:
    """Chunk with its computed relevance score from search."""
    chunk: ChunkRecord
    score: float = 0.0


class MemoryVectorStore:
    """Enhanced pure-Python vector store with n-gram hashing, BM25 and keyword boosting."""

    VECTOR_SIZE = 512  # increased from 256 for richer representation

    def __init__(self) -> None:
        self.chunks: list[ChunkRecord] = []
        self._vectors: list[list[float]] = []
        # BM25 index
        self._doc_freqs: Counter[str] = Counter()  # token -> num docs containing it
        self._avg_dl: float = 0.0  # average document length (in tokens)
        self._doc_lens: list[int] = []  # per-chunk token count
        self._doc_tokens: list[set[str]] = []  # per-chunk token sets

    @property
    def backend_name(self) -> str:
        return "memory"

    # ── Embedding with n-gram hashing ──────────────────────────────

    @staticmethod
    def _ngrams(tokens: list[str], n: int = 2) -> list[str]:
        """Generate character n-grams and word bigrams for richer representation."""
        result: list[str] = []
        # Word-level bigrams
        for i in range(len(tokens) - 1):
            result.append(f"{tokens[i]}_{tokens[i + 1]}")
        # Character trigrams for each token (captures morphological similarity)
        for token in tokens:
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    result.append(f"c3:{token[i:i + 3]}")
        return result

    def _embed(self, text: str) -> list[float]:
        """Create embedding using unigram + n-gram hashing for semantic richness."""
        vec = [0.0] * self.VECTOR_SIZE
        tokens = tokenize(text)
        if not tokens:
            return vec

        # Unigrams (weight 1.0)
        all_features: list[tuple[str, float]] = [(t, 1.0) for t in tokens]
        # Bigrams + char trigrams (weight 0.5 — secondary signal)
        for ng in self._ngrams(tokens):
            all_features.append((ng, 0.5))

        for feature, weight in all_features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            # Use two slots per feature for denser signal
            slot1 = int.from_bytes(digest[:4], "little") % self.VECTOR_SIZE
            slot2 = int.from_bytes(digest[4:8], "little") % self.VECTOR_SIZE
            sign1 = 1.0 if digest[8] % 2 == 0 else -1.0
            sign2 = 1.0 if digest[9] % 2 == 0 else -1.0
            vec[slot1] += sign1 * weight
            vec[slot2] += sign2 * weight * 0.5

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 8) for x in vec]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
        norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (norm_a * norm_b)

    # ── BM25 scoring ──────────────────────────────────────────────

    def _bm25_score(self, query_tokens: set[str], doc_idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        """Compute BM25 score for a document given query tokens."""
        if not query_tokens or not self._doc_tokens:
            return 0.0
        n = len(self.chunks)
        dl = self._doc_lens[doc_idx]
        score = 0.0
        for qt in query_tokens:
            df = self._doc_freqs.get(qt, 0)
            if df == 0:
                continue
            # IDF component
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            # TF component (binary: 1 if present, 0 otherwise — sufficient for short chunks)
            tf = 1.0 if qt in self._doc_tokens[doc_idx] else 0.0
            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / (self._avg_dl or 1.0))
            score += idf * numerator / denominator
        return score

    # ── Keyword boosting ──────────────────────────────────────────

    @staticmethod
    def _keyword_boost(query: str, chunk: ChunkRecord) -> float:
        """Bonus score when query matches document keywords explicitly."""
        if not chunk.keywords:
            return 0.0
        query_lower = query.lower()
        hits = sum(1 for kw in chunk.keywords if kw.lower() in query_lower)
        return min(0.3, hits * 0.1)  # up to 0.3 bonus

    # ── Doc-type relevance bonus ──────────────────────────────────

    @staticmethod
    def _doc_type_bonus(doc_type: str) -> float:
        """Strategy and KPI docs get a small relevance boost."""
        bonuses = {"strategy": 0.05, "kpi": 0.04, "manager_goal": 0.03, "vnd": 0.02}
        return bonuses.get(doc_type, 0.0)

    # ── Indexing ──────────────────────────────────────────────────

    def index_documents(self, documents: list[Document]) -> int:
        self.chunks.clear()
        self._vectors.clear()
        self._doc_freqs.clear()
        self._doc_lens.clear()
        self._doc_tokens.clear()

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

                # Embed title + text + keywords together
                embed_text = f"{doc.title} {part} {' '.join(doc.keywords)}"
                self._vectors.append(self._embed(embed_text))

                # BM25 index: tokenize and record
                tokens = set(tokenize(f"{part} {' '.join(doc.keywords)}"))
                self._doc_tokens.append(tokens)
                self._doc_lens.append(len(tokens))
                for t in tokens:
                    self._doc_freqs[t] += 1

        # Compute average document length for BM25
        self._avg_dl = sum(self._doc_lens) / len(self._doc_lens) if self._doc_lens else 0.0
        return len(self.chunks)

    # ── Search (hybrid: cosine + BM25 + keyword boost) ────────────

    def search(
        self,
        query: str,
        department_id: str | None = None,
        top_k: int = 5,
    ) -> list[ChunkRecord]:
        """Search returning ChunkRecords (backward-compatible)."""
        scored = self.search_scored(query, department_id, top_k)
        return [sc.chunk for sc in scored]

    def search_scored(
        self,
        query: str,
        department_id: str | None = None,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Enhanced hybrid search returning chunks with relevance scores.

        Scoring: cosine(0.40) + BM25(0.35) + keyword_boost(0.15) + doc_type(0.10)
        """
        if not self.chunks:
            return []

        query_vec = self._embed(query)
        query_tokens = set(tokenize(query))

        scored: list[ScoredChunk] = []
        for idx, (chunk, vec) in enumerate(zip(self.chunks, self._vectors)):
            # Filter by department scope
            if department_id:
                if chunk.department_scope and department_id not in chunk.department_scope:
                    if chunk.owner_department_id != department_id:
                        continue

            cos = max(0.0, self._cosine(query_vec, vec))
            bm25 = self._bm25_score(query_tokens, idx)
            # Normalize BM25 to [0,1] range (heuristic: cap at 10)
            bm25_norm = min(1.0, bm25 / 10.0) if bm25 > 0 else 0.0
            kw_boost = self._keyword_boost(query, chunk)
            dt_bonus = self._doc_type_bonus(chunk.doc_type)

            final = cos * 0.40 + bm25_norm * 0.35 + kw_boost * 0.15 + dt_bonus * 0.10
            scored.append(ScoredChunk(chunk=chunk, score=round(final, 4)))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
