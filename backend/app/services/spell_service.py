"""Spell correction service with edit distance, candidate generation, and ranking."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger("nebula.spell")


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    # NFKD decomposes accents; combining marks are then stripped
    normalized = unicodedata.normalize("NFKD", text)
    # Strip combining characters
    no_accents = "".join(c for c in normalized if not unicodedata.combining(c))
    # Remove control characters (codepoint < 32 except tab/newline, and DEL)
    no_control = "".join(c for c in no_accents if not (ord(c) < 32 and c not in ("\t", "\n")))
    # Lowercase
    lowered = no_control.lower()
    # Collapse whitespace
    collapsed = re.sub(r"\s+", " ", lowered).strip()
    return collapsed


# ---------------------------------------------------------------------------
# Levenshtein distance (restricted to max_distance to bound cost)
# ---------------------------------------------------------------------------


def levenshtein_distance(s1: str, s2: str, max_distance: int = 2) -> int:
    """Return Levenshtein distance between two strings, bounded by max_distance."""
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > max_distance:
        return max_distance + 1

    # Ensure s1 is the shorter string to minimize space
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1

    previous = list(range(len1 + 1))
    current = [0] * (len1 + 1)

    for i in range(1, len2 + 1):
        current[0] = i
        if min(current) > max_distance:
            return max_distance + 1
        for j in range(1, len1 + 1):
            cost = 0 if s1[j - 1] == s2[i - 1] else 1
            current[j] = min(
                previous[j] + 1,     # deletion
                current[j - 1] + 1,  # insertion
                previous[j - 1] + cost,  # substitution
            )
            if current[j] > max_distance:
                current[j] = max_distance + 1
        if min(current) > max_distance:
            return max_distance + 1
        previous, current = current, previous

    result = previous[len1]
    return result if result <= max_distance else max_distance + 1


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class SpellResult:
    original: str
    corrected: str
    confidence: float
    changed: bool
    suggestions: list[str] | None = None


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------


def _generate_candidates(word: str, dictionary: set[str], max_distance: int = 2) -> set[str]:
    """Generate candidate corrections using edit operations."""
    candidates: set[str] = set()
    n = len(word)
    if n == 0:
        return candidates

    # Direct dictionary lookup
    if word in dictionary:
        candidates.add(word)

    # Check strings at edit distance 1
    for i in range(n):
        # deletion
        d = word[:i] + word[i + 1 :]
        if d in dictionary:
            candidates.add(d)
        for c in "abcdefghijklmnopqrstuvwxyz":
            # substitution
            s = word[:i] + c + word[i + 1 :]
            if s in dictionary:
                candidates.add(s)
        # insertion
        for c in "abcdefghijklmnopqrstuvwxyz":
            ins = word[:i] + c + word[i:]
            if ins in dictionary:
                candidates.add(ins)
    # insertion at end
    for c in "abcdefghijklmnopqrstuvwxyz":
        ins = word + c
        if ins in dictionary:
            candidates.add(ins)
    # transposition
    for i in range(n - 1):
        t = word[:i] + word[i + 1] + word[i] + word[i + 2 :]
        if t in dictionary:
            candidates.add(t)

    # If no candidates at distance 1, try distance 2 (limit cost)
    if not candidates and max_distance >= 2:
        for cand in list(candidates):
            for i in range(len(cand)):
                d2 = cand[:i] + cand[i + 1 :]
                if d2 in dictionary:
                    candidates.add(d2)
                for c in "abcdefghijklmnopqrstuvwxyz":
                    s2 = cand[:i] + c + cand[i + 1 :]
                    if s2 in dictionary:
                        candidates.add(s2)

    return candidates


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def _rank_candidates(
    word: str,
    candidates: set[str],
    frequency: dict[str, int],
    max_distance: int = 2,
) -> list[tuple[str, float]]:
    """Return (candidate, score) sorted descending."""
    scored: list[tuple[str, float]] = []
    max_freq = max(frequency.values()) if frequency else 1
    for cand in candidates:
        dist = levenshtein_distance(word, cand, max_distance=max_distance)
        if dist > max_distance:
            continue
        # scores (0..1)
        edit_score = max(0.0, 1.0 - dist / (max_distance + 1))
        freq_score = frequency.get(cand, 0) / max_freq if max_freq > 0 else 0.0
        prefix_score = 1.0 if cand.startswith(word[: min(3, len(word))]) else 0.0
        popularity = min(1.0, frequency.get(cand, 0) / 10000)  # arbitrary cap
        confidence = (
            0.45 * edit_score + 0.30 * freq_score + 0.15 * prefix_score + 0.10 * popularity
        )
        scored.append((cand, round(confidence, 4)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SpellService:
    """Production spell correction with Redis-backed caching."""

    def __init__(self, cache_client, dictionary: set[str] | None = None, frequency: dict[str, int] | None = None):
        self._cache = cache_client
        self._dictionary: set[str] = dictionary if dictionary is not None else set()
        self._frequency: dict[str, int] = frequency if frequency is not None else {}
        self._cache_prefix = "spell:"
        self._cache_ttl = 3600  # 1 hour
        self._max_distance = 2
        self._default_distance = 1

    def _cache_key(self, query: str) -> str:
        normalized = normalize_text(query)
        return f"{self._cache_prefix}{hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()}"

    def _build_default_english(self) -> set[str]:
        words = set()
        try:
            import enchant
            enchant.Dict("en_US")
            # Enchant doesn't expose a word list directly; try wordlist file
            for path in (
                "/usr/share/dict/words",
                "/usr/dict/words",
                "C:/words.txt",
            ):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            w = line.strip().lower()
                            if w:
                                words.add(w)
                    if words:
                        break
                except FileNotFoundError:
                    continue
        except Exception as exc:
            logger.debug("Spell dictionary file load failed: %s", exc)
        return words

    async def load_dictionary(self) -> None:
        """Load dictionary from DB and in-memory cache if available."""
        try:
            from app.database.engine import connect
            from app.database.repositories.spell import SpellRepository  # type: ignore
            db = await connect()
            repo = SpellRepository(db)
            words = await repo.get_all_words()
            self._dictionary = set(words)
            freq = await repo.get_all_frequencies()
            self._frequency = freq
            await db.close()
        except Exception as exc:
            logger.warning("Falling back to default dictionary: %s", exc)
            self._dictionary = self._build_default_english()
            self._frequency = {w: 1 for w in self._dictionary}
        if not self._dictionary:
            self._dictionary = self._build_default_english()
            self._frequency = {w: 1 for w in self._dictionary}

    async def update_dictionary(self, words: list[str]) -> None:
        """Update dictionary with new words extracted from indexed documents."""
        for w in words:
            w = normalize_text(w)
            if not w or any(c.isdigit() for c in w):
                continue
            self._dictionary.add(w)
            self._frequency[w] = self._frequency.get(w, 0) + 1

    async def _get_cached(self, query: str) -> SpellResult | None:
        if not self._cache:
            return None
        key = self._cache_key(query)
        try:
            data = await self._cache.get(key)
            if data:
                return SpellResult(**data)
        except Exception:
            return None
        return None

    async def _set_cached(self, query: str, result: SpellResult) -> None:
        if not self._cache:
            return
        key = self._cache_key(query)
        try:
            await self._cache.set(key, result.__dict__, ttl=self._cache_ttl)
        except Exception as exc:
            logger.debug("Spell cache set failed: %s", exc)

    async def correct_query(
        self,
        query: str,
        max_distance: int = 2,
        default_distance: int = 1,
    ) -> SpellResult:
        self._max_distance = max_distance
        self._default_distance = default_distance
        normalized = normalize_text(query)

        # Validate
        if not normalized or len(normalized) > 100:
            return SpellResult(
                original=query,
                corrected=normalized or query,
                confidence=1.0 if not normalized else 0.0,
                changed=False,
            )

        # Try cache
        cached = await self._get_cached(normalized)
        if cached:
            cached.original = query
            return cached

        tokens = normalized.split(" ")
        corrected_tokens: list[str] = []
        any_changed = False
        best_confidence = 1.0
        suggestions: list[str] | None = []

        for token in tokens:
            if not token:
                corrected_tokens.append(token)
                continue
            if token in self._dictionary:
                corrected_tokens.append(token)
                continue

            candidates = _generate_candidates(token, self._dictionary, max_distance=self._max_distance)
            if token in candidates:
                candidates.add(token)
            ranked = _rank_candidates(token, candidates, self._frequency, max_distance=self._max_distance)
            if not ranked:
                corrected_tokens.append(token)
                continue
            best, confidence = ranked[0]
            corrected_tokens.append(best)
            if best != token:
                any_changed = True
            if confidence < best_confidence:
                best_confidence = confidence
            for cand, _ in ranked[:5]:
                if cand not in suggestions:
                    suggestions.append(cand)

        corrected = " ".join(corrected_tokens)
        confidence = round(best_confidence, 4)
        result = SpellResult(
            original=query,
            corrected=corrected,
            confidence=confidence,
            changed=any_changed,
            suggestions=suggestions[:5] if suggestions else None,
        )
        await self._set_cached(normalized, result)
        return result

    async def generate_candidates(self, word: str, max_distance: int = 2) -> list[str]:
        normalized = normalize_text(word)
        if not normalized:
            return []
        candidates = _generate_candidates(normalized, self._dictionary, max_distance=max_distance)
        ranked = _rank_candidates(normalized, candidates, self._frequency, max_distance=max_distance)
        return [c for c, _ in ranked[:10]]