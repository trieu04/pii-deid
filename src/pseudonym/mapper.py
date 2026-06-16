from cachetools import LRUCache

from src.models import EntityType
from src.pseudonym.generator import generate_pseudonym


# maxsize: max unique pseudonym mappings held in memory
_mapping_cache: LRUCache = LRUCache(maxsize=50000)


def get_pseudonym(entity_type: EntityType, original: str, salt: str) -> str:
    """Deterministic: same (type, value, salt) → same output across calls."""
    cache_key = f"{salt}:{entity_type.value}:{original}"
    if cache_key in _mapping_cache:
        return _mapping_cache[cache_key]

    pseudonym = generate_pseudonym(entity_type, original, salt)
    _mapping_cache[cache_key] = pseudonym
    return pseudonym


def cache_size() -> int:
    return len(_mapping_cache)
