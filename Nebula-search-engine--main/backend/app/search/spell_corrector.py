"""Spell correction for search queries."""

import logging
import os
from collections import Counter
from difflib import SequenceMatcher
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger("nebula.search.spell")

settings = get_settings()


class SpellCorrector:
    """Spell correction using edit distance and corpus frequency."""

    def __init__(self, max_suggestions: int = 5):
        self.max_suggestions = max_suggestions
        self._word_frequency: Counter = Counter()
        self._vocabulary: set = set()

    def load_from_index(self, inverted_index) -> None:
        """
        Load vocabulary and word frequencies from inverted index.
        
        Args:
            inverted_index: InvertedIndexBuilder instance
        """
        try:
            self._vocabulary = inverted_index._vocabulary
            # Calculate word frequencies from term frequencies
            for doc_tf in inverted_index._term_frequencies.values():
                self._word_frequency.update(doc_tf)
            logger.info("Loaded %d words for spell correction", len(self._vocabulary))
        except Exception as exc:
            logger.error("Failed to load spell correction data: %s", exc)

    def correct_query(self, query: str) -> tuple[str, bool]:
        """
        Correct spelling in query.
        
        Args:
            query: Input query
            
        Returns:
            Tuple of (corrected_query, was_corrected)
        """
        words = query.lower().split()
        corrected_words = []
        was_corrected = False

        for word in words:
            if word in self._vocabulary:
                corrected_words.append(word)
            else:
                correction = self._correct_word(word)
                if correction and correction != word:
                    corrected_words.append(correction)
                    was_corrected = True
                    logger.debug("Corrected '%s' to '%s'", word, correction)
                else:
                    corrected_words.append(word)

        corrected_query = " ".join(corrected_words)
        return corrected_query, was_corrected

    def _correct_word(self, word: str) -> Optional[str]:
        """
        Get correction for a single word.
        
        Args:
            word: Word to correct
            
        Returns:
            Corrected word or None
        """
        if not self._vocabulary or len(word) < 3:
            return None

        # Generate candidates
        candidates = self._generate_candidates(word)
        if not candidates:
            return None

        # Rank candidates by frequency and similarity
        scored = []
        for candidate in candidates:
            similarity = SequenceMatcher(None, word, candidate).ratio()
            frequency = self._word_frequency.get(candidate, 1)
            # Combine similarity and frequency
            score = similarity * 0.7 + min(frequency / 1000, 1.0) * 0.3
            scored.append((score, candidate))

        scored.sort(reverse=True)
        return scored[0][1] if scored else None

    def _generate_candidates(self, word: str) -> List[str]:
        """
        Generate candidate corrections.
        
        Args:
            word: Word to correct
            
        Returns:
            List of candidate words
        """
        candidates = set()

        # Words at edit distance 1
        for candidate in self._edits1(word):
            if candidate in self._vocabulary:
                candidates.add(candidate)

        # If no candidates at distance 1, try distance 2
        if not candidates:
            for candidate in self._edits2(word):
                if candidate in self._vocabulary:
                    candidates.add(candidate)

        return list(candidates)

    def _edits1(self, word: str) -> List[str]:
        """Generate all edits at distance 1."""
        letters = "abcdefghijklmnopqrstuvwxyz"
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]

        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]

        return deletes + transposes + replaces + inserts

    def _edits2(self, word: str) -> List[str]:
        """Generate all edits at distance 2."""
        return [e2 for e1 in self._edits1(word) for e2 in self._edits1(e1)]

    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get query suggestions based on similar queries.
        
        Args:
            query: Input query
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        # This would use query log to find similar past queries
        # For now, return simple word-based suggestions
        words = query.lower().split()
        suggestions = []

        for word in words:
            if word not in self._vocabulary:
                correction = self._correct_word(word)
                if correction:
                    suggestions.append(correction)

        return suggestions[:limit]


# Global instance
spell_corrector = SpellCorrector()