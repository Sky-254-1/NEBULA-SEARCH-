"""BM25 scoring engine for keyword-based retrieval.

Implements BM25Okapi with field-level weighting,
stop word handling, and efficient pre-computation.
"""

import math
import re
import logging
from collections import Counter
from typing import Optional

logger = logging.getLogger("nebula.vector.bm25")

# Standard English stop words
_STOP_WORDS: set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with", "the", "this", "but", "not",
    "or", "what", "which", "who", "whom", "how", "when", "where",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "they", "them", "their", "do", "does", "did",
}


def tokenize(text: str, remove_stop_words: bool = True) -> list[str]:
    """Tokenize text into lowercase words, optionally removing stop words."""
    tokens = re.findall(r"\w+(?:'\w+)?", text.lower())
    if remove_stop_words:
        return [t for t in tokens if t not in _STOP_WORDS]
    return tokens


class BM25Okapi:
    """BM25-Okapi ranking function.

    k1: Controls term frequency saturation (default 1.2-1.6)
    b: Controls document length normalization (0=barely, 1=full)
    delta: Term frequency lower bound
    """

    def __init__(
        self,
        corpus: Optional[list[str]] = None,
        k1: float = 1.5,
        b: float = 0.75,
        delta: float = 0.5,
    ):
        self.k1 = k1
        self.b = b
        self.delta = delta
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: list[Counter] = []
        self.idf: dict[str, float] = {}
        self.doc_len: list[int] = []

        if corpus:
            self.build(corpus)

    def build(self, corpus: list[str]) -> None:
        """Build BM25 index from a list of documents."""
        self.corpus_size = len(corpus)
        self.doc_freqs = []
        self.doc_len = []
        df: dict[str, int] = {}

        for document in corpus:
            tokens = tokenize(document)
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            self.doc_len.append(len(tokens))

            for term in freq:
                df[term] = df.get(term, 0) + 1

        self.avgdl = sum(self.doc_len) / self.corpus_size if self.corpus_size > 0 else 0.0

        # Compute IDF
        self.idf = {}
        for term, freq in df.items():
            idf = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[term] = idf

    def score(self, query: str, doc_index: int) -> float:
        """Compute BM25 score for a single document."""
        if doc_index < 0 or doc_index >= self.corpus_size:
            return 0.0

        query_tokens = tokenize(query)
        if not query_tokens:
            return 0.0

        doc_freq = self.doc_freqs[doc_index]
        doc_len = self.doc_len[doc_index]

        score = 0.0
        for term in query_tokens:
            if term not in self.idf:
                continue

            tf = doc_freq.get(term, 0)
            tf = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
            score += self.idf[term] * tf

        return score

    def scores(self, query: str) -> list[float]:
        """Compute BM25 scores for all documents."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return [0.0] * self.corpus_size

        scores = []
        for i in range(self.corpus_size):
            scores.append(self.score(query, i))
        return scores

    def top_k(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        """Return top-k (index, score) pairs."""
        all_scores = self.scores(query)
        indexed = [(i, s) for i, s in enumerate(all_scores) if s > 0]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[:k]


class FieldAwareBM25:
    """BM25 with per-field weights (title, content) for structured documents."""

    def __init__(self, field_weights: Optional[dict[str, float]] = None):
        self.field_weights = field_weights or {"title": 2.0, "content": 1.0}
        self._indexes: dict[str, BM25Okapi] = {}

    def add_field(self, name: str, corpus: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        """Add a BM25 index for a specific field."""
        self._indexes[name] = BM25Okapi(corpus, k1=k1, b=b)

    def score(self, query: str, doc_index: int) -> float:
        """Compute weighted BM25 score across all fields."""
        total = 0.0
        for field, index in self._indexes.items():
            weight = self.field_weights.get(field, 1.0)
            total += weight * index.score(query, doc_index)
        return total

    def top_k(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        """Return top-k results across all fields."""
        combined: dict[int, float] = {}
        for field, index in self._indexes.items():
            weight = self.field_weights.get(field, 1.0)
            for doc_idx, score in index.top_k(query, k=k * 2):
                combined[doc_idx] = combined.get(doc_idx, 0) + weight * score

        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]