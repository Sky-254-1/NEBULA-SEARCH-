"""
Synonym Expansion Module

Expands search queries with synonyms to improve recall:
- Domain-specific synonym dictionaries
- Acronym expansion
- Multilingual synonyms
- Context-aware expansion
"""

import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)


class SynonymExpander:
    """
    Expands search queries with synonyms.
    
    Supports multiple expansion strategies and languages.
    """
    
    # Common synonym mappings
    SYNONYM_DICTIONARIES = {
        'en': {
            # Technology
            'ai': ['artificial intelligence', 'machine learning', 'ml'],
            'ml': ['machine learning', 'ai', 'artificial intelligence'],
            'api': ['application programming interface', 'rest api', 'web api'],
            'ui': ['user interface', 'frontend', 'gui'],
            'ux': ['user experience', 'usability', 'design'],
            'db': ['database', 'data storage', 'dbms'],
            'sql': ['structured query language', 'database query'],
            'nosql': ['non-relational database', 'document database'],
            'cloud': ['cloud computing', 'saas', 'paas', 'iaas'],
            'devops': ['development operations', 'ci/cd', 'automation'],
            'frontend': ['client-side', 'ui', 'user interface'],
            'backend': ['server-side', 'api', 'server'],
            'fullstack': ['full stack', 'full-stack'],
            
            # Common words
            'buy': ['purchase', 'acquire', 'get'],
            'sell': ['vend', 'market', 'trade'],
            'cheap': ['inexpensive', 'affordable', 'budget'],
            'expensive': ['costly', 'pricey', 'high-priced'],
            'fast': ['quick', 'rapid', 'speedy'],
            'slow': ['sluggish', 'unfast', 'leisurely'],
            'big': ['large', 'huge', 'enormous', 'giant'],
            'small': ['tiny', 'little', 'miniature', 'compact'],
            'good': ['excellent', 'great', 'quality', 'superb'],
            'bad': ['poor', 'terrible', 'awful', 'inferior'],
            'happy': ['pleased', 'satisfied', 'delighted', 'joyful'],
            'sad': ['unhappy', 'depressed', 'miserable', 'sorrowful'],
            'help': ['assist', 'aid', 'support', 'guide'],
            'problem': ['issue', 'trouble', 'difficulty', 'challenge'],
            'solution': ['answer', 'fix', 'resolution', 'remedy'],
            'create': ['make', 'build', 'generate', 'produce'],
            'delete': ['remove', 'erase', 'destroy', 'eliminate'],
            'update': ['modify', 'change', 'upgrade', 'refresh'],
            'find': ['search', 'locate', 'discover', 'identify'],
            'show': ['display', 'view', 'present', 'reveal'],
            'hide': ['conceal', 'mask', 'cover', 'obscure'],
        },
        'es': {
            'ia': ['inteligencia artificial', 'aprendizaje automatico'],
            'api': ['interfaz de programacion', 'api rest'],
            'computadora': ['ordenador', 'pc', 'equipo'],
            'coche': ['carro', 'vehiculo', 'auto'],
            'comprar': ['adquirir', 'obtener', 'adquirir'],
            'vender': ['comercializar', 'tradear', 'ofrecer'],
            'ayuda': ['asistencia', 'soporte', 'auxilio'],
            'problema': ['inconveniente', 'dificultad', 'contratiempo'],
            'solucion': ['respuesta', 'resolucion', 'remedio'],
        },
        'fr': {
            'ia': ['intelligence artificielle', 'apprentissage automatique'],
            'api': ['interface de programmation', 'api rest'],
            'ordinateur': ['pc', 'machine', 'calculateur'],
            'voiture': ['auto', 'vehicule', 'automobile'],
            'acheter': ['acquérir', 'se procurer', 'obtenir'],
            'vendre': ['commercialiser', 'ecouler', 'offrir'],
            'aide': ['assistance', 'soutien', 'secours'],
            'probleme': ['difficulte', 'ennui', 'contrariete'],
            'solution': ['reponse', 'resolution', 'remede'],
        },
    }
    
    # Acronym expansions
    ACRONYMS = {
        'en': {
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'nlp': 'natural language processing',
            'api': 'application programming interface',
            'rest': 'representational state transfer',
            'json': 'javascript object notation',
            'xml': 'extensible markup language',
            'html': 'hypertext markup language',
            'css': 'cascading style sheets',
            'js': 'javascript',
            'ts': 'typescript',
            'db': 'database',
            'sql': 'structured query language',
            'nosql': 'non-relational database',
            'orm': 'object-relational mapping',
            'mvc': 'model-view-controller',
            'spa': 'single page application',
            'pwa': 'progressive web app',
            'seo': 'search engine optimization',
            'ux': 'user experience',
            'ui': 'user interface',
            'ci': 'continuous integration',
            'cd': 'continuous deployment',
            'devops': 'development and operations',
            'saas': 'software as a service',
            'paas': 'platform as a service',
            'iaas': 'infrastructure as a service',
            'vpn': 'virtual private network',
            'dns': 'domain name system',
            'cdn': 'content delivery network',
            'ssl': 'secure sockets layer',
            'tls': 'transport layer security',
            'jwt': 'json web token',
            'oauth': 'open authorization',
            'sso': 'single sign-on',
            'mfa': 'multi-factor authentication',
            '2fa': 'two-factor authentication',
        },
        'es': {
            'ia': 'inteligencia artificial',
            'api': 'interfaz de programacion de aplicaciones',
            'bd': 'base de datos',
            'sql': 'lenguaje de consulta estructurado',
            'ui': 'interfaz de usuario',
            'ux': 'experiencia de usuario',
        },
        'fr': {
            'ia': 'intelligence artificielle',
            'api': 'interface de programmation',
            'bd': 'base de donnees',
            'sql': 'langage de requete structure',
            'ui': 'interface utilisateur',
            'ux': 'experience utilisateur',
        },
    }
    
    def __init__(
        self,
        language: str = 'en',
        enable_synonyms: bool = True,
        enable_acronyms: bool = True,
        max_synonyms_per_word: int = 3,
    ):
        """
        Initialize synonym expander.
        
        Args:
            language: Language code (default: 'en')
            enable_synonyms: Enable synonym expansion (default: True)
            enable_acronyms: Enable acronym expansion (default: True)
            max_synonyms_per_word: Maximum synonyms per word (default: 3)
        """
        self.language = language
        self.enable_synonyms = enable_synonyms
        self.enable_acronyms = enable_acronyms
        self.max_synonyms_per_word = max_synonyms_per_word
        self._cache: dict[str, list[str]] = {}
    
    async def expand(self, query: str) -> dict:
        """
        Expand query with synonyms and acronyms.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with original and expanded queries
        """
        if not query:
            return {
                'original': query,
                'expanded': query,
                'synonyms_added': [],
            }
        
        # Check cache
        cache_key = (query, self.language, self.enable_synonyms, self.enable_acronyms)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        expanded_terms = []
        synonyms_added = []
        
        # Tokenize query
        words = query.lower().split()
        
        # Expand each word
        for word in words:
            # Clean word (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word)
            
            # Add synonyms
            if self.enable_synonyms and clean_word in self.SYNONYM_DICTIONARIES.get(self.language, {}):
                synonyms = self.SYNONYM_DICTIONARIES[self.language][clean_word][:self.max_synonyms_per_word]
                expanded_terms.extend(synonyms)
                synonyms_added.extend(synonyms)
            
            # Expand acronyms
            if self.enable_acronyms and clean_word in self.ACRONYMS.get(self.language, {}):
                acronym_expansion = self.ACRONYMS[self.language][clean_word]
                expanded_terms.append(acronym_expansion)
                synonyms_added.append(acronym_expansion)
        
        # Build expanded query
        all_terms = words + expanded_terms
        expanded_query = ' '.join(all_terms)
        
        result = {
            'original': query,
            'expanded': expanded_query,
            'synonyms_added': synonyms_added,
        }
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    async def expand_for_search(self, query: str) -> str:
        """
        Expand query and return expanded version for search.
        
        Args:
            query: Search query
            
        Returns:
            Expanded query string
        """
        result = await self.expand(query)
        return result['expanded']
    
    def add_synonym(self, word: str, synonyms: list[str], language: Optional[str] = None):
        """
        Add custom synonym mapping.
        
        Args:
            word: Base word
            synonyms: List of synonyms
            language: Language code (uses instance language if not provided)
        """
        lang = language or self.language
        
        if lang not in self.SYNONYM_DICTIONARIES:
            self.SYNONYM_DICTIONARIES[lang] = {}
        
        self.SYNONYM_DICTIONARIES[lang][word.lower()] = synonyms
        self._cache.clear()
    
    def add_acronym(self, acronym: str, expansion: str, language: Optional[str] = None):
        """
        Add custom acronym expansion.
        
        Args:
            acronym: Acronym
            expansion: Full expansion
            language: Language code (uses instance language if not provided)
        """
        lang = language or self.language
        
        if lang not in self.ACRONYMS:
            self.ACRONYMS[lang] = {}
        
        self.ACRONYMS[lang][acronym.lower()] = expansion
        self._cache.clear()
    
    def clear_cache(self):
        """Clear expansion cache."""
        self._cache.clear()


# Singleton instance
synonym_expander = SynonymExpander()