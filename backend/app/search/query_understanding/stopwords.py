"""
Stop-Word Removal Module

Removes stop words from search queries:
- Multilingual stop word lists
- Configurable stop words
- Context-aware stop word handling
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StopWordRemover:
    """
    Removes stop words from search queries.
    
    Supports multiple languages with extensible stop word lists.
    """
    
    # Common stop words for multiple languages
    STOP_WORDS = {
        'en': {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
            'have', 'had', 'what', 'when', 'where', 'who', 'which', 'why',
            'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'can', 'just', 'should',
            'now', 'also', 'into', 'over', 'after', 'before', 'between',
            'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'up', 'down', 'out', 'off', 'about', 'against', 'during',
            'without', 'through', 'during', 'before', 'after', 'above',
            'below', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once',
        },
        'es': {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o',
            'pero', 'si', 'no', 'porque', 'como', 'cuando', 'donde', 'quien',
            'cual', 'que', 'en', 'de', 'a', 'para', 'por', 'con', 'sin',
            'sobre', 'entre', 'hacia', 'desde', 'hasta', 'durante', 'mediante',
            'según', 'contra', 'bajo', 'sobre', 'tras', 'versus', 'vía',
            'es', 'son', 'era', 'eran', 'fue', 'fueron', 'ser', 'será',
            'tener', 'tiene', 'tenido', 'ha', 'han', 'había', 'habían',
            'muy', 'mucho', 'poco', 'bastante', 'demasiado', 'algo',
            'nada', 'todo', 'todos', 'cada', 'varios', 'ciertos',
        },
        'fr': {
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'donc',
            'or', 'ni', 'car', 'si', 'que', 'qui', 'quoi', 'dont', 'où',
            'en', 'dans', 'sur', 'sous', 'vers', 'par', 'pour', 'avec',
            'sans', 'entre', 'depuis', 'pendant', 'pour', 'contre', 'chez',
            'est', 'sont', 'était', 'étaient', 'fut', 'furent', 'sera',
            'avoir', 'a', 'ont', 'avait', 'avaient', 'eu', 'très', 'beaucoup',
            'peu', 'assez', 'trop', 'tout', 'tous', 'chaque', 'certains',
            'quelques', 'aucun', 'ni', 'pas', 'jamais', 'toujours',
        },
        'de': {
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer',
            'einem', 'einen', 'und', 'oder', 'aber', 'denn', 'sondern', 'doch',
            'wie', 'was', 'wer', 'wenn', 'dass', 'ob', 'obwohl', 'während',
            'in', 'an', 'auf', 'aus', 'bei', 'für', 'gegen', 'mit', 'nach',
            'seit', 'von', 'zu', 'bis', 'durch', 'ohne', 'um', 'ist', 'sind',
            'war', 'waren', 'wird', 'werden', 'haben', 'hat', 'hatte', 'sehr',
            'viel', 'wenig', 'genug', 'alle', 'jede', 'jeder', 'einige',
            'keine', 'nicht', 'nie', 'immer',
        },
        'it': {
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'e', 'o',
            'ma', 'perché', 'quindi', 'anzi', 'infatti', 'però', 'se', 'che',
            'chi', 'cosa', 'quale', 'quanto', 'dove', 'quando', 'come',
            'in', 'di', 'a', 'da', 'per', 'con', 'su', 'tra', 'fra', 'verso',
            'è', 'sono', 'era', 'erano', 'fu', 'furon', 'essere', 'avere',
            'ha', 'hanno', 'aveva', 'molto', 'poco', 'tutto', 'tutti',
            'ogni', 'alcuni', 'nessuno', 'non', 'mai', 'sempre',
        },
        'pt': {
            'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'e', 'ou',
            'mas', 'porque', 'portanto', 'pois', 'contudo', 'se', 'que',
            'quem', 'qual', 'onde', 'quando', 'como', 'em', 'de', 'para',
            'por', 'com', 'sem', 'sobre', 'entre', 'desde', 'até', 'é',
            'são', 'era', 'eram', 'foi', 'foram', 'ser', 'ter', 'tem',
            'tinha', 'muito', 'pouco', 'tudo', 'todos', 'cada', 'alguns',
            'nenhum', 'não', 'nunca', 'sempre',
        },
        'ru': {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'за',
            'под', 'над', 'при', 'через', 'между', 'это', 'этот', 'эта',
            'эти', 'тот', 'та', 'те', 'как', 'что', 'кто', 'где', 'когда',
            'почему', 'зачем', 'какой', 'какая', 'какое', 'какие', 'есть',
            'быть', 'был', 'была', 'было', 'были', 'иметь', 'имеет',
            'очень', 'много', 'мало', 'все', 'всё', 'каждый', 'некоторые',
            'никакой', 'не', 'никогда', 'всегда',
        },
    }
    
    def __init__(self, language: str = 'en', custom_stop_words: Optional[list[str]] = None):
        """
        Initialize stop word remover.
        
        Args:
            language: Language code (default: 'en')
            custom_stop_words: Additional custom stop words to add
        """
        self.language = language
        self.stop_words = self._load_stop_words(language)
        
        # Add custom stop words
        if custom_stop_words:
            self.stop_words.update(custom_stop_words)
        
        self._cache: dict[str, list[str]] = {}
    
    def _load_stop_words(self, language: str) -> set[str]:
        """
        Load stop words for a language.
        
        Args:
            language: Language code
            
        Returns:
            Set of stop words
        """
        # Return stop words for the language, or English as fallback
        return self.STOP_WORDS.get(language, self.STOP_WORDS['en']).copy()
    
    async def remove_stop_words(self, tokens: list[str]) -> list[str]:
        """
        Remove stop words from a list of tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of tokens with stop words removed
        """
        if not tokens:
            return []
        
        # Filter out stop words (case-insensitive)
        filtered = [
            token for token in tokens
            if token.lower() not in self.stop_words
        ]
        
        return filtered
    
    async def process(self, query: str) -> dict:
        """
        Process a query by removing stop words.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with original and filtered tokens
        """
        if not query:
            return {
                'original': [],
                'filtered': [],
                'removed_count': 0,
            }
        
        # Tokenize (simple whitespace split)
        tokens = query.lower().split()
        
        # Remove stop words
        filtered = await self.remove_stop_words(tokens)
        
        return {
            'original': tokens,
            'filtered': filtered,
            'removed_count': len(tokens) - len(filtered),
        }
    
    def add_stop_words(self, words: list[str]):
        """
        Add custom stop words.
        
        Args:
            words: List of stop words to add
        """
        self.stop_words.update(word.lower() for word in words)
        self._cache.clear()
    
    def remove_stop_words_from_list(self, words: list[str]):
        """
        Remove stop words from the stop word list.
        
        Args:
            words: List of stop words to remove
        """
        self.stop_words -= set(word.lower() for word in words)
        self._cache.clear()
    
    def get_stop_words(self) -> list[str]:
        """
        Get current stop words list.
        
        Returns:
            Sorted list of stop words
        """
        return sorted(list(self.stop_words))
    
    def clear_cache(self):
        """Clear cache."""
        self._cache.clear()

    def remove(self, tokens: list[str], language: str = 'en') -> list[str]:
        """
        Remove stop words from tokens (synchronous alias for pipeline compatibility).
        
        Args:
            tokens: List of tokens
            language: Language code (ignored, uses instance language)
            
        Returns:
            List of tokens with stop words removed
        """
        if not tokens:
            return []
        filtered = [
            token for token in tokens
            if token.lower() not in self.stop_words
        ]
        return filtered


# Singleton instance
stop_word_remover = StopWordRemover()

# Alias for backward compatibility
StopwordRemover = StopWordRemover
